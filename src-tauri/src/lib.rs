mod storage;
use serde::{Deserialize, Serialize};
use std::{path::PathBuf, sync::{Mutex, atomic::{AtomicBool, Ordering}}};
use tauri::{AppHandle, Emitter, Manager, State, WebviewWindow, LogicalSize, PhysicalPosition, WindowEvent,
    menu::{Menu, MenuItem}, tray::TrayIconBuilder};
struct AppStorage { directory: PathBuf, writer: Mutex<()>, tray_ready: AtomicBool }
#[derive(Serialize, Deserialize)]
struct Placement { x: i32, y: i32 }
fn caller(window: &WebviewWindow) -> Result<(), String> {
    if window.label() == "main" { Ok(()) } else { Err("Unrecognized window".into()) }
}
fn keep_on_screen(window: &WebviewWindow) -> tauri::Result<()> {
    let pos=window.outer_position()?; let size=window.outer_size()?;
    let visible=window.available_monitors()?.iter().any(|m| {
        let p=m.position(); let s=m.size();
        i64::from(pos.x)+i64::from(size.width) > i64::from(p.x)+64 &&
        i64::from(pos.y)+i64::from(size.height) > i64::from(p.y)+64 &&
        i64::from(pos.x)+64 < i64::from(p.x)+i64::from(s.width) &&
        i64::from(pos.y)+64 < i64::from(p.y)+i64::from(s.height)
    });
    if !visible { window.center()?; }
    Ok(())
}
fn fit_expanded(window: &WebviewWindow) -> tauri::Result<()> {
    let mut width: f64=1000.0;let mut height: f64=800.0;
    if let Some(m)=window.current_monitor()?.or(window.primary_monitor()?) {
        let logical=m.size().to_logical::<f64>(m.scale_factor());
        width=width.min((logical.width-48.0).max(280.0));
        height=height.min((logical.height-80.0).max(380.0));
    }
    window.set_size(LogicalSize::new(width,height))?;keep_on_screen(window)
}
fn save_placement(window: &WebviewWindow) -> Result<(), String> {
    let app=window.app_handle();let state=app.state::<AppStorage>();
    let _guard=state.writer.lock().map_err(|_| "Storage writer unavailable")?;
    let p=window.outer_position().map_err(|_| "Could not read window placement")?;
    let raw=serde_json::to_string(&Placement{x:p.x,y:p.y}).map_err(|_| "Invalid placement")?;
    storage::write_atomic(&state.directory.join("placement.json"),&raw)
}
fn recover(app: &AppHandle) {
    if let Some(w)=app.get_webview_window("main") {
        let result=(|| -> tauri::Result<()> {
            w.set_ignore_cursor_events(false)?;w.unminimize()?;keep_on_screen(&w)?;w.show()?;w.set_focus()?;w.emit("desktop-visibility",true)?;Ok(())
        })();
        if let Err(e)=result { eprintln!("Could not recover Emberwish: {e}"); }
    }
}
#[tauri::command]
fn load_state(window: WebviewWindow, state: State<'_,AppStorage>) -> Result<Option<String>,String> {
    caller(&window)?;
    let _guard=state.writer.lock().map_err(|_| "Storage writer unavailable")?;
    storage::read_bounded(&state.directory.join("ritual.json"),storage::MAX_BYTES)
}
#[tauri::command]
fn save_state(window: WebviewWindow, state: State<'_,AppStorage>, json: String) -> Result<(),String> {
    caller(&window)?;storage::validate(&json,storage::now_ms()?)?;
    let _guard=state.writer.lock().map_err(|_| "Storage writer unavailable")?;
    storage::write_atomic(&state.directory.join("ritual.json"),&json)
}
#[tauri::command]
fn desktop_action(window: WebviewWindow, state: State<'_,AppStorage>, action: String) -> Result<(),String> {
    caller(&window)?;
    if ["hide","click_through"].contains(&action.as_str()) && !state.tray_ready.load(Ordering::SeqCst) {
        return Err("Tray unavailable; hiding/click-through disabled to preserve recovery".into());
    }
    let result=(|| -> tauri::Result<()> {
        match action.as_str() {
            "compact" => { window.set_resizable(false)?;window.set_size(LogicalSize::new(300.0,440.0))?;keep_on_screen(&window)?; }
            "expand" => { window.set_ignore_cursor_events(false)?;window.set_resizable(true)?;fit_expanded(&window)?; }
            "pin" => window.set_always_on_top(true)?,
            "unpin" => window.set_always_on_top(false)?,
            "hide" => { let _=save_placement(&window);window.emit("desktop-visibility",false)?;if let Err(e)=window.hide(){let _=window.emit("desktop-visibility",true);return Err(e);} }
            "click_through" => window.set_ignore_cursor_events(true)?,
            "drag" => window.start_dragging()?,
            "quit" => { let _=save_placement(&window);window.app_handle().exit(0); }
            _ => return Ok(()),
        }
        Ok(())
    })();
    if !["compact","expand","pin","unpin","hide","click_through","drag","quit"].contains(&action.as_str()) {return Err("Unknown desktop action".into());}
    result.map_err(|_| "Desktop action failed".into())
}
fn install_tray(app: &mut tauri::App) -> tauri::Result<()> {
    let show=MenuItem::with_id(app,"show","Show & interact",true,None::<&str>)?;
    let reset=MenuItem::with_id(app,"reset","Bring to screen center",true,None::<&str>)?;
    let hide=MenuItem::with_id(app,"hide","Hide",true,None::<&str>)?;
    let quit=MenuItem::with_id(app,"quit","Quit Emberwish",true,None::<&str>)?;
    let force=MenuItem::with_id(app,"force-quit","Force quit (discard unsaved changes)",true,None::<&str>)?;
    let menu=Menu::with_items(app,&[&show,&reset,&hide,&quit,&force])?;
    let mut builder=TrayIconBuilder::with_id("emberwish-tray").tooltip("Emberwish").menu(&menu).show_menu_on_left_click(true)
        .on_menu_event(|app,event| {
            match event.id.as_ref() {
                "show" => recover(app),
                "reset" => {if let Some(w)=app.get_webview_window("main"){let _=w.center();}recover(app);}
                "hide" => {if let Some(w)=app.get_webview_window("main"){let _=w.emit("request-hide",());}}
                "quit" => {if let Some(w)=app.get_webview_window("main"){let _=w.emit("request-quit",());}}
                "force-quit" => app.exit(0),
                _ => {}
            }
        });
    if let Some(icon)=app.default_window_icon(){builder=builder.icon(icon.clone());}
    builder.build(app)?;
    app.state::<AppStorage>().tray_ready.store(true,Ordering::SeqCst);
    Ok(())
}
#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_single_instance::init(|app,_,_|recover(app)))
        .setup(|app| {
            let directory=app.path().app_data_dir()?;
            app.manage(AppStorage{directory:directory.clone(),writer:Mutex::new(()),tray_ready:AtomicBool::new(false)});
            if let Some(w)=app.get_webview_window("main") {
                if let Ok(Some(raw))=storage::read_bounded(&directory.join("placement.json"),1024) {
                    if let Ok(p)=serde_json::from_str::<Placement>(&raw){let _=w.set_position(PhysicalPosition::new(p.x,p.y));let _=keep_on_screen(&w);}
                }
            }
            if let Err(e)=install_tray(app){eprintln!("Tray unavailable; unsafe hide controls will be disabled: {e}");}
            Ok(())
        })
        .on_window_event(|window,event| {
            if let WindowEvent::CloseRequested {api,..}=event {
                let state=window.state::<AppStorage>();
                if state.tray_ready.load(Ordering::SeqCst) {api.prevent_close();let _=window.emit("request-hide",());}
            }
        })
        .invoke_handler(tauri::generate_handler![load_state,save_state,desktop_action])
        .run(tauri::generate_context!())
        .expect("Emberwish could not start");
}
