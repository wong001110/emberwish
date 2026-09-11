//! App-owned, bounded persistence. No path supplied by the renderer is accepted.
use serde::Deserialize;
use std::{fs::{self, File, OpenOptions}, io::{Read, Write}, path::Path, time::{SystemTime, UNIX_EPOCH}};
pub const MAX_BYTES: usize = 16_384;
#[derive(Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
struct Snapshot {
    version: u8, wish_draft: String, duration_minutes: u32,
    sound_enabled: bool, reduce_motion: bool, pinned: bool, view: String, ritual: Ritual,
}
#[derive(Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
struct Ritual { status: String, started_at: Option<u64>, ended_at: Option<u64>, duration_ms: u64, wish: String }
fn clean_text(value: &str) -> bool {
    value.chars().count() <= 160 && !value.chars().any(|c| c.is_control() && c != '\n' && c != '\t')
}
pub fn validate(raw: &str, now: u64) -> Result<(), String> {
    if raw.len() > MAX_BYTES { return Err("Saved state is too large".into()); }
    let s: Snapshot = serde_json::from_str(raw).map_err(|_| "Invalid state schema")?;
    let _preferences = (s.sound_enabled, s.reduce_motion, s.pinned);
    if s.version != 1 || ![5,15,30].contains(&s.duration_minutes) || !["expanded","compact"].contains(&s.view.as_str()) || !clean_text(&s.wish_draft) || !clean_text(&s.ritual.wish) {
        return Err("Invalid preferences".into());
    }
    let r = s.ritual;
    if ![300_000,900_000,1_800_000].contains(&r.duration_ms) { return Err("Invalid burn duration".into()); }
    if r.status == "idle" {
        return if r.started_at.is_none() && r.ended_at.is_none() { Ok(()) } else { Err("Idle ritual contains timestamps".into()) };
    }
    let start = r.started_at.ok_or("Missing start time")?;
    if start > now || start > 9_007_199_254_740_991 { return Err("Invalid start time".into()); }
    let end = start + r.duration_ms;
    match r.status.as_str() {
        "burning" if r.ended_at.is_none() => Ok(()),
        "completed" if r.ended_at == Some(end) && end <= now => Ok(()),
        "extinguished" if r.ended_at.is_some_and(|t| t >= start && t <= now && t <= end) => Ok(()),
        _ => Err("Invalid ritual transition".into()),
    }
}
pub fn now_ms() -> Result<u64, String> {
    Ok(SystemTime::now().duration_since(UNIX_EPOCH).map_err(|_| "Invalid system clock")?.as_millis() as u64)
}
pub fn read_bounded(path: &Path, limit: usize) -> Result<Option<String>, String> {
    let file = match File::open(path) {
        Ok(f) => f,
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => return Ok(None),
        Err(_) => return Err("Could not open app data".into()),
    };
    let mut bytes = Vec::new();
    file.take((limit + 1) as u64).read_to_end(&mut bytes).map_err(|_| "Could not read app data")?;
    if bytes.len() > limit { return Err("App data exceeds its size limit".into()); }
    String::from_utf8(bytes).map(Some).map_err(|_| "App data is not UTF-8".into())
}
pub fn write_atomic(path: &Path, raw: &str) -> Result<(), String> {
    let dir = path.parent().ok_or("Invalid app data directory")?;
    fs::create_dir_all(dir).map_err(|_| "Could not create app data directory")?;
    let temp = path.with_extension("tmp");
    let mut file = OpenOptions::new().write(true).create(true).truncate(true).open(&temp).map_err(|_| "Could not create app data snapshot")?;
    file.write_all(raw.as_bytes()).and_then(|_| file.sync_all()).map_err(|_| "Could not flush app data")?;
    drop(file);
    // rename replaces the previous file only after the new snapshot is flushed.
    fs::rename(&temp, path).map_err(|_| "Could not replace app data snapshot".to_string())
}
#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::{json, Value};
    fn value() -> Value { json!({"version":1,"wishDraft":"平安","durationMinutes":5,"soundEnabled":false,"reduceMotion":false,"pinned":false,"view":"expanded","ritual":{"status":"burning","startedAt":1000,"endedAt":null,"durationMs":300000,"wish":"平安"}}) }
    #[test] fn valid_active_state() { assert!(validate(&value().to_string(),2000).is_ok()); }
    #[test] fn unknown_fields_are_rejected() { let mut v=value();v["command"]=json!("anything");assert!(validate(&v.to_string(),2000).is_err()); }
    #[test] fn invalid_clock_and_duration() { let mut v=value();assert!(validate(&v.to_string(),999).is_err());v["ritual"]["durationMs"]=json!(1);assert!(validate(&v.to_string(),2000).is_err()); }
    #[test] fn bounds_and_invalid_text() { assert!(validate(&"x".repeat(MAX_BYTES+1),2000).is_err());let mut v=value();v["wishDraft"]=json!("x".repeat(161));assert!(validate(&v.to_string(),2000).is_err());v["wishDraft"]=json!("\u{0}");assert!(validate(&v.to_string(),2000).is_err()); }
    #[test] fn completion_and_extinguish_invariants() { let mut v=value();v["ritual"]["status"]=json!("completed");v["ritual"]["endedAt"]=json!(2000);assert!(validate(&v.to_string(),302000).is_err());v["ritual"]["endedAt"]=json!(301000);assert!(validate(&v.to_string(),302000).is_ok());v["ritual"]["status"]=json!("extinguished");v["ritual"]["endedAt"]=json!(1500);assert!(validate(&v.to_string(),2000).is_ok()); }
    #[test] fn atomic_replace_roundtrip_and_bounded_reads() {
        let dir=std::env::temp_dir().join(format!("emberwish-test-{}-{}",std::process::id(),SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_nanos()));
        let path=dir.join("ritual.json");
        assert_eq!(read_bounded(&path,MAX_BYTES).unwrap(),None);
        write_atomic(&path,"first").unwrap();write_atomic(&path,"second").unwrap();
        assert_eq!(read_bounded(&path,MAX_BYTES).unwrap(),Some("second".into()));
        assert!(read_bounded(&path,2).is_err());assert!(!path.with_extension("tmp").exists());
        fs::remove_dir_all(dir).unwrap();
    }
}
