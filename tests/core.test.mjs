import test from 'node:test';
import assert from 'node:assert/strict';
import { defaults, light, advance, extinguish, fraction, remaining, restore, cleanWish, shouldAnimate } from '../.test-build/core.js';
import { StateWriter } from '../.test-build/platform.js';
const now = 1_700_000_000_000;
const burn = () => light({...defaults(), wishDraft:'平安落地', durationMinutes:5}, now);
test('fresh defaults are isolated, silent and not running',()=>{ const a=defaults(),b=defaults(); a.wishDraft='x'; assert.equal(b.wishDraft,''); assert.equal(a.soundEnabled,false); assert.equal(a.ritual.status,'idle'); });
test('lighting captures the wish and configured duration',()=>{const s=burn();assert.equal(s.ritual.wish,'平安落地'); assert.equal(s.ritual.durationMs,300000);assert.equal(s.ritual.startedAt,now);});
test('lighting twice cannot restart a running ritual',()=>{const s=burn();assert.equal(light(s,now+5000),s);});
test('completion uses the exact deadline even after a long hidden interval',()=>{const s=advance(burn(),now+600000);assert.equal(s.ritual.status,'completed');assert.equal(s.ritual.endedAt,now+300000);});
test('progress is elapsed time, not render count',()=>{assert.equal(fraction(burn().ritual,now+150000),.5);assert.equal(remaining(burn().ritual,now+150000),'02:30');});
test('clock rollback clamps elapsed progress without generating negatives',()=>assert.equal(fraction(burn().ritual,now-10000),0));
test('extinguish freezes progress and restart creates a new ritual',()=>{const s=extinguish(burn(),now+120000);assert.equal(s.ritual.status,'extinguished');assert.equal(fraction(s.ritual,now+200000),.4);assert.equal(light(s,now+200000).ritual.startedAt,now+200000);});
test('an already elapsed ritual completes instead of extinguishing late',()=>assert.equal(extinguish(burn(),now+400000).ritual.status,'completed'));
test('invalid observation times are rejected',()=>{for(const t of [NaN,Infinity,-1,1.2]){assert.throws(()=>light(defaults(),t));assert.throws(()=>advance(burn(),t));assert.throws(()=>extinguish(burn(),t));}});
test('wish clipping counts codepoints, removes controls, never evaluates markup',()=>{assert.equal(Array.from(cleanWish('龍'.repeat(161))).length,160);assert.equal(cleanWish('\0hello\x01'), 'hello');assert.equal(cleanWish('<script>x</script>'),'<script>x</script>');});
test('restore null is clean and completed-on-restart state is derived',()=>{assert.equal(restore(null,now).warning,null);assert.equal(restore(JSON.stringify(burn()),now+400000).state.ritual.status,'completed');});
test('active state roundtrips without reset',()=>{const result=restore(JSON.stringify(burn()),now+5000);assert.equal(result.warning,null);assert.deepEqual(result.state,burn());});
for(const [label,mutate] of [
 ['version',s=>s.version=2],['future start',s=>s.ritual.startedAt=now+1000],['duration',s=>s.ritual.durationMs=1],
 ['bad end',s=>s.ritual.endedAt=now],['invalid status',s=>s.ritual.status='done'],['array',()=>[]],
 ['unsafe timestamp',s=>s.ritual.startedAt=Number.MAX_SAFE_INTEGER+10],['wrong type',s=>s.pinned='false'],
 ['partial completed',s=>{s.ritual.status='completed';s.ritual.endedAt=now+1000;}],
])test(`restore rejects ${label}`,()=>{const s=burn();const replacement=mutate(s);const r=restore(JSON.stringify(Array.isArray(replacement)?replacement:s),now);assert.ok(r.warning);assert.equal(r.state.ritual.status,'idle');});
test('oversize and malformed state fail without throwing',()=>{for(const value of ['{', 'x'.repeat(16385)])assert.ok(restore(value,now).warning);});
test('renderer policy is quiet for idle, hidden and reduced motion',()=>{assert.ok(shouldAnimate(true,true,false));for(const p of [[false,true,false],[true,false,false],[true,true,true]])assert.equal(shouldAnimate(...p),false);});
test('same-tick saves keep newest data (FND-001)',async()=>{let stored;const writer=new StateWriter(()=>assert.fail('unexpected storage error'),async json=>{stored=json;});const a=defaults();const p=writer.save({...a,wishDraft:'first'});const q=writer.save({...a,wishDraft:'last'});await Promise.all([p,q]);assert.equal(JSON.parse(stored).wishDraft,'last');});
test('slow native-like write cannot overwrite newer state',async()=>{const writes=[];let release;const held=new Promise(resolve=>release=resolve);let n=0;const writer=new StateWriter(()=>{},async json=>{if(n++===0)await held;writes.push(JSON.parse(json).wishDraft);});const p=writer.save({...defaults(),wishDraft:'first'});await Promise.resolve();writer.save({...defaults(),wishDraft:'second'});const q=writer.save({...defaults(),wishDraft:'newest'});release();await Promise.all([p,q]);assert.deepEqual(writes,['first','newest']);});
test('failed storage is surfaced and a later change can retry',async()=>{let count=0,stored=null;const errors=[];const writer=new StateWriter(e=>errors.push(e),async json=>{if(count++===0)throw Error('disk');stored=json;});await writer.save(defaults());await writer.save({...defaults(),wishDraft:'retry'});assert.equal(errors.length,1);assert.equal(JSON.parse(stored).wishDraft,'retry');});
test('a save in a microtask after draining is not stranded',async()=>{let stored;const writer=new StateWriter(()=>{},async json=>{stored=json;});const p=writer.save({...defaults(),wishDraft:'first'});await Promise.resolve();await Promise.resolve();const q=writer.save({...defaults(),wishDraft:'late'});await Promise.all([p,q]);assert.equal(JSON.parse(stored).wishDraft,'late');});
test('C1 control characters are removed before native serialization',()=>assert.equal(cleanWish('a\u0085b\u009fc'),'abc'));
test('save status prevents a clean-quit claim after a rejected write',async()=>{let reject=true;const writer=new StateWriter(()=>{},async()=>{if(reject)throw Error('disk');});await writer.save(defaults());assert.equal(writer.lastSaveSucceeded,false);reject=false;await writer.save(defaults());assert.equal(writer.lastSaveSucceeded,true);});
