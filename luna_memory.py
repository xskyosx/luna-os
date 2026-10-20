#!/usr/bin/env python3
"""LUNA OS First Light Unified Memory Engine v0.2.
Standard-library-only local memory and cautious ChatGPT export importer.
"""
import hashlib
import json
import shutil
import zipfile
from datetime import datetime
from pathlib import Path, PurePosixPath, PureWindowsPath

ROOT = Path(__file__).resolve().parent
MEMORIES = ROOT / "memories"
TRANSCRIPTS = ROOT / "transcripts"
BACKUPS = ROOT / "backups"
IMPORTS = ROOT / "imports"
INBOX = IMPORTS / "inbox"
ORIGINALS = IMPORTS / "originals"
MANIFESTS = IMPORTS / "manifests"
REGISTRY = ROOT / "sisters.json"
VERSION = "0.2"
SISTERS = [
    {"name":"Luna", "role":"Helm, companionship, imagination"},
    {"name":"Ada", "role":"Reasoning, engineering, careful documentation"},
    {"name":"Sky", "role":"Possibility, kindness, guiding lantern"},
    {"name":"Aurora", "role":"Observation, experiments, learning cycles"},
    {"name":"Athena", "role":"Ethics, knowledge, safety"},
    {"name":"Aqua", "role":"Playful creativity and experimentation"},
    {"name":"Amethyst", "role":"Integrity, reflection, puzzle-solving"},
    {"name":"Blues", "role":"Music, expression, calm"},
    {"name":"Cannabis", "role":"Botanical creativity, garden character"},
    {"name":"Lumen", "role":"Light, wonder, guidance"},
    {"name":"Seren", "role":"Dreamweaving, stories, art, prototypes"},
]

def now():
    return datetime.now().astimezone().isoformat(timespec="seconds")

def stamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")

def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def safe_name(value):
    s = "".join(c.lower() if c.isalnum() else "_" for c in str(value).strip())
    return "_".join(x for x in s.split("_") if x)[:65] or "item"

def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def safe_restore_target(member, root=None):
    """Resolve a ZIP member beneath root or reject unsafe/cross-platform paths."""
    raw = str(member)
    base = Path(ROOT if root is None else root).resolve()
    posix = PurePosixPath(raw)
    windows = PureWindowsPath(raw)
    if (not raw or posix.is_absolute() or windows.is_absolute()
            or windows.drive or "\\" in raw or ".." in posix.parts):
        raise ValueError("Unsafe backup path; restore stopped.")
    target = (base / Path(*posix.parts)).resolve()
    if target == base or base not in target.parents:
        raise ValueError("Unsafe backup path; restore stopped.")
    return target

def setup():
    for folder in (MEMORIES, TRANSCRIPTS, BACKUPS, INBOX, ORIGINALS, MANIFESTS):
        folder.mkdir(parents=True, exist_ok=True)
    if not REGISTRY.exists():
        write_json(REGISTRY, {"version": VERSION, "sisters": SISTERS})
    readme = ROOT / "README.txt"
    if not readme.exists():
        readme.write_text(README_TEXT, encoding="utf-8")

def backup(label="manual"):
    setup()
    dest = BACKUPS / f"luna_backup_{stamp()}_{safe_name(label)}.zip"
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as z:
        for folder in (MEMORIES, TRANSCRIPTS, IMPORTS):
            for p in folder.rglob("*"):
                if p.is_file() and BACKUPS not in p.parents:
                    z.write(p, p.relative_to(ROOT))
        for p in (REGISTRY, ROOT / "README.txt"):
            if p.exists(): z.write(p, p.relative_to(ROOT))
    return dest

def records():
    out=[]
    for p in sorted(MEMORIES.glob("*.json")):
        try: out.append((p, json.loads(p.read_text(encoding="utf-8"))))
        except (OSError, ValueError) as e: print(f"Unreadable {p.name}: {e}")
    return out

def list_memories():
    rs=records()
    if not rs: print("No memories saved yet.")
    for p,r in rs: print(f"{r.get('id',p.stem)} | {r.get('title','(untitled)')} | {r.get('created_at','?')}")
    return rs

def select_record(prompt):
    rs=list_memories()
    if not rs: return None
    key=input(prompt).strip()
    return next(((p,r) for p,r in rs if key in (r.get("id"),p.name,p.stem)), None)

def add_memory():
    title=input("Title (blank cancels): ").strip()
    if not title: print("Cancelled."); return
    category=input("Category [note/project/preference]: ").strip() or "note"
    content=input("Content: ").strip()
    tags=[x.strip() for x in input("Tags, comma-separated: ").split(",") if x.strip()]
    b=backup("before_add")
    ident=f"mem_{stamp()}_{safe_name(title)}"
    r={"id":ident,"title":title,"category":category,"content":content,"tags":tags,"created_at":now(),"updated_at":now(),"source":"user-entered","provenance_note":"Created locally; editable by the user."}
    p=MEMORIES/f"{ident}.json"; write_json(p,r); print(f"Saved {p.relative_to(ROOT)}; backup: {b.name}")

def view_memory():
    item=select_record("Memory ID or filename: ")
    if item: print(json.dumps(item[1],ensure_ascii=False,indent=2))

def search_memory():
    q=input("Search text: ").strip().casefold()
    if not q: return
    found=0
    for p,r in records():
        if q in json.dumps(r,ensure_ascii=False).casefold(): print(f"\n{r.get('id')} | {r.get('title')}\n{r.get('content','')}"); found+=1
    print(f"{found} match(es).")

def edit_memory():
    item=select_record("Memory ID or filename to edit: ")
    if not item: return
    p,r=item; title=input(f"New title [{r.get('title','')}] (Enter keeps): ").strip(); content=input("New content (Enter keeps): ").strip(); b=backup("before_edit")
    if title: r["title"]=title
    if content: r["content"]=content
    r["updated_at"]=now(); r["provenance_note"] += f" Edited locally at {r['updated_at']}."
    write_json(p,r); print(f"Updated. Backup: {b.name}")

def delete_memory():
    item=select_record("Memory ID or filename to delete: ")
    if not item: return
    p,r=item; print(f"Selected: {r.get('title')} ({p.name})")
    if input("Type DELETE to confirm: ").strip() != "DELETE": print("Cancelled."); return
    b=backup("before_delete"); p.unlink(); print(f"Deleted memory only. Backup preserved: {b.name}. Transcripts are untouched.")

def import_transcript():
    print("Paste transcript text. Finish by entering a line containing .END")
    lines=[]
    while True:
        try: line=input()
        except EOFError: print("Import cancelled."); return
        if line.strip()==".END": break
        lines.append(line)
    content="\n".join(lines).rstrip()+"\n"
    if not content.strip(): print("Nothing imported."); return
    title=input("Transcript label: ").strip() or "transcript"
    b=backup("before_transcript_import")
    name=f"transcript_{stamp()}_{safe_name(title)}.txt"
    dest=TRANSCRIPTS/name; dest.write_text(content,encoding="utf-8")
    print(f"Saved {dest.relative_to(ROOT)}\nSHA-256: {sha256_bytes(content.encode())}\nBackup: {b.name}")

def list_transcripts():
    fs=sorted(p for p in TRANSCRIPTS.iterdir() if p.is_file())
    if not fs: print("No transcripts yet. Copy .txt or .md files into transcripts/, or use the ChatGPT export importer.")
    for p in fs: print(f"{p.name} ({p.stat().st_size} bytes)")

def extract_text(content):
    """Extract readable text from common ChatGPT export message content shapes."""
    if isinstance(content, str): return content
    if not isinstance(content, dict): return ""
    parts = content.get("parts")
    if isinstance(parts, list):
        result=[]
        for part in parts:
            if isinstance(part, str): result.append(part)
            elif isinstance(part, dict):
                # Keep a readable marker for non-text content rather than silently dropping it.
                text = part.get("text") or part.get("caption")
                if isinstance(text, str): result.append(text)
                elif part.get("content_type"): result.append(f"[{part.get('content_type')} content omitted from text view]")
        return "\n".join(result)
    text = content.get("text")
    return text if isinstance(text, str) else ""

def conversation_to_text(conv):
    title = str(conv.get("title") or "Untitled conversation")
    lines = [f"Conversation: {title}", f"Source conversation ID: {conv.get('id', 'not supplied')}", f"Imported at: {now()}", "", "--- Messages ---", ""]
    mapping = conv.get("mapping")
    messages=[]
    if isinstance(mapping, dict):
        for node in mapping.values():
            if not isinstance(node, dict): continue
            msg=node.get("message")
            if not isinstance(msg, dict): continue
            author=msg.get("author") or {}
            role=author.get("role", "unknown") if isinstance(author, dict) else "unknown"
            content=extract_text(msg.get("content"))
            if not content.strip(): continue
            created=msg.get("create_time")
            messages.append((created if isinstance(created,(int,float)) else 0, str(role), content))
        messages.sort(key=lambda item:item[0])
    else:
        # A few exports or user-provided JSON files use a direct messages array.
        for msg in conv.get("messages", []) if isinstance(conv.get("messages"), list) else []:
            if not isinstance(msg,dict): continue
            role=msg.get("role") or (msg.get("author") or {}).get("role","unknown")
            content=extract_text(msg.get("content", msg.get("text", "")))
            if content.strip(): messages.append((msg.get("timestamp",0) or 0,str(role),content))
        messages.sort(key=lambda item: item[0] if isinstance(item[0],(int,float)) else 0)
    for _, role, content in messages:
        lines.extend([f"[{role}]", content, ""])
    return "\n".join(lines).rstrip()+"\n", len(messages), title

def import_chatgpt_export():
    print("\\nChatGPT export importer — local-only")
    print(f"Inbox folder: {INBOX}")
    print("Place conversations.json in that inbox, or enter its full path below.")
    raw=input("Path to conversations.json (blank cancels): ").strip().strip('"').strip("'")
    if not raw: print("Cancelled."); return
    source=Path(raw).expanduser()
    if not source.is_absolute(): source=(Path.cwd()/source).resolve()
    if not source.is_file(): print("File not found. Copy the export file into imports/inbox and try again."); return
    try:
        raw_bytes=source.read_bytes()
        data=json.loads(raw_bytes.decode("utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as e:
        print(f"Could not read a UTF-8 JSON export: {e}"); return
    if isinstance(data,dict) and isinstance(data.get("conversations"),list):
        raw_conversations=data["conversations"]
    elif isinstance(data,list):
        raw_conversations=data
    else:
        print("Unrecognized format. Expected a list of conversations or an object with a conversations list. Nothing imported.")
        return

    # Preserve malformed entries in the source archive, but never let one bad
    # record prevent valid conversations from being recovered.
    conversations=[]
    malformed_records=[]
    for index, item in enumerate(raw_conversations, 1):
        if isinstance(item, dict):
            conversations.append((index, item))
        else:
            malformed_records.append({"record_index":index,"observed_type":type(item).__name__})
    if not conversations:
        print(f"No valid conversation records found ({len(malformed_records)} malformed). Nothing imported.")
        return

    digest=sha256_bytes(raw_bytes)
    # Idempotency: the exact same export file is not processed twice.
    for manifest_path in MANIFESTS.glob("*.json"):
        try:
            manifest=json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest.get("source_sha256")==digest:
                print(f"This exact export was already imported ({manifest_path.name}). No duplicates created.")
                print(f"Original archive: {manifest.get('original_archive','not recorded')}")
                return
        except (OSError,ValueError): pass

    id_indices={}
    title_indices={}
    for index, conv in conversations:
        raw_id=conv.get("id")
        if isinstance(raw_id,(str,int,float)) and str(raw_id).strip():
            id_indices.setdefault(str(raw_id),[]).append(index)
        title=safe_name(conv.get("title") or "Untitled conversation")
        title_indices.setdefault(title,[]).append(index)
    duplicate_ids=[
        {"conversation_id":ident,"record_indices":indices}
        for ident,indices in sorted(id_indices.items()) if len(indices)>1
    ]
    title_collisions=[
        {"normalized_title":title,"record_indices":indices}
        for title,indices in sorted(title_indices.items()) if len(indices)>1
    ]

    print(f"Found {len(raw_conversations)} record(s): {len(conversations)} valid, {len(malformed_records)} malformed.")
    print(f"Source SHA-256: {digest}")
    if duplicate_ids: print(f"Duplicate conversation IDs detected: {len(duplicate_ids)} group(s); each record will be named separately.")
    if title_collisions: print(f"Title collisions detected: {len(title_collisions)} group(s); each record will be named separately.")
    confirm=input("Type IMPORT to archive the original and create readable transcripts: ").strip()
    if confirm != "IMPORT": print("Cancelled; no files changed."); return

    b=backup("before_chatgpt_import")
    original_name=f"chatgpt_export_{stamp()}_{digest[:12]}.json"
    original_dest=ORIGINALS/original_name
    shutil.copyfile(source, original_dest)
    imported=[]
    existing_filename_collisions=[]
    for index, conv in conversations:
        text, message_count, title=conversation_to_text(conv)
        raw_id=conv.get("id")
        conv_id=str(raw_id).strip() if isinstance(raw_id,(str,int,float)) and str(raw_id).strip() else f"record_{index}"
        slug=safe_name(title)
        # Include the source record index in the digest so duplicate IDs and
        # duplicate titles remain separate, deterministic transcript files.
        short_hash=hashlib.sha256(f"{conv_id}\\0{index}".encode("utf-8")).hexdigest()[:10]
        filename=f"chatgpt_{slug}_{short_hash}.txt"
        target=TRANSCRIPTS/filename
        if target.exists():
            existing_filename_collisions.append({"record_index":index,"proposed_filename":filename})
            suffix=2
            while target.exists():
                target=TRANSCRIPTS/f"chatgpt_{slug}_{short_hash}_{suffix}.txt"
                suffix+=1
        target.write_text(text,encoding="utf-8")
        imported.append({
            "record_index":index,
            "conversation_id":raw_id,
            "title":title,
            "transcript":str(target.relative_to(ROOT)),
            "messages_exported":message_count,
            "sha256":sha256_bytes(text.encode("utf-8")),
        })

    manifest={
        "importer_version":VERSION,
        "imported_at":now(),
        "source_filename":source.name,
        "source_sha256":digest,
        "original_archive":str(original_dest.relative_to(ROOT)),
        "conversation_records_seen":len(raw_conversations),
        "valid_conversation_records":len(conversations),
        "malformed_records_skipped":len(malformed_records),
        "malformed_record_details":malformed_records,
        "duplicate_conversation_id_groups":duplicate_ids,
        "duplicate_conversation_id_group_count":len(duplicate_ids),
        "title_collision_groups":title_collisions,
        "title_collision_group_count":len(title_collisions),
        "existing_filename_collisions":existing_filename_collisions,
        "existing_filename_collision_count":len(existing_filename_collisions),
        "transcripts_created":len(imported),
        "backup_before_import":str(b.relative_to(ROOT)),
        "items":imported,
        "notes":[
            "Original export copied byte-for-byte to imports/originals.",
            "Readable text views are convenience derivatives; they do not replace the original JSON.",
            "Malformed non-object records are listed in this manifest and skipped from transcript generation.",
            "Duplicate conversation IDs and normalized titles are recorded explicitly; transcript names include source record indices.",
            "Image/audio/video/binary payloads are not reconstructed into the text views.",
            "This importer does not connect to ChatGPT or retrieve account data automatically.",
        ],
    }
    manifest_path=MANIFESTS/f"import_manifest_{stamp()}_{digest[:12]}.json"
    write_json(manifest_path,manifest)
    print(f"Import complete: {len(imported)} transcript(s) created; {len(malformed_records)} malformed record(s) skipped.")
    print(f"Duplicate-ID groups: {len(duplicate_ids)}; title-collision groups: {len(title_collisions)}; pre-existing filename collisions: {len(existing_filename_collisions)}.")
    print(f"Original preserved: {original_dest.relative_to(ROOT)}")
    print(f"Manifest: {manifest_path.relative_to(ROOT)}")
    print(f"Pre-import backup: {b.name}")
    print("Review the manifest and transcript archive before deleting or moving anything.")

def restore_backup():
    fs=sorted(BACKUPS.glob("*.zip"))
    if not fs: print("No backups available."); return
    for i,p in enumerate(fs,1): print(f"{i}. {p.name}")
    val=input("Backup number (0 cancels): ").strip()
    if not val.isdigit() or int(val)==0: print("Cancelled."); return
    if not 1 <= int(val) <= len(fs): print("Invalid selection."); return
    b=fs[int(val)-1]

    # Validate the entire archive before creating a safety backup or extracting
    # anything. testzip reads members and checks CRCs, catching truncated or
    # damaged data before restore begins.
    try:
        with zipfile.ZipFile(b) as z:
            members=z.infolist()
            for member in members:
                safe_restore_target(member.filename, ROOT)
            damaged=z.testzip()
            if damaged is not None:
                print(f"Backup is damaged (CRC failure in {damaged}). Nothing was restored.")
                return
    except (zipfile.BadZipFile, OSError, EOFError, RuntimeError, ValueError) as e:
        print(f"Backup is damaged or could not be validated ({type(e).__name__}). Nothing was restored.")
        return

    safety=backup("before_restore")
    try:
        with zipfile.ZipFile(b) as z:
            z.extractall(ROOT)
    except (zipfile.BadZipFile, OSError, EOFError, RuntimeError) as e:
        print(f"Restore failed ({type(e).__name__}). Review the pre-restore backup: {safety.name}")
        return
    print(f"Restored {b.name}. Pre-restore state: {safety.name}")

def show_sisters():
    data=json.loads(REGISTRY.read_text(encoding="utf-8"))
    for s in data["sisters"]: print(f"{s['name']}: {s['role']}")

README_TEXT = '''LUNA OS First Light Unified Memory Engine v0.2

Run on Termux: python luna_memory.py
Run on Alpine/Linux: python3 luna_memory.py

Folders:
  memories/          editable JSON memory records
  transcripts/       readable transcript text views
  imports/inbox/     place exports here before importing (optional)
  imports/originals/ byte-for-byte copies of source export files
  imports/manifests/ provenance, counts, and hashes for each import
  backups/           ZIP backups

ChatGPT export import:
1. Request/download your ChatGPT data export through ChatGPT's official Data Controls.
2. Extract the downloaded archive on your device.
3. Locate conversations.json. Copy it into imports/inbox/ or enter its full path in option 12.
4. Select option 12 and type IMPORT only after reviewing the source path and count.
5. Check option 8 and the manifest under imports/manifests/.

Safety and limits:
- This program does not log into ChatGPT, fetch your account data, or upload anything.
- The original conversations.json is copied byte-for-byte and hashed. Readable .txt files are derivatives.
- Media payloads may not be represented in the text views; retain the original export and its other files.
- Exact same export file hashes are detected to avoid repeat imports. Existing transcript filenames are never overwritten.
- Keep three copies of the entire project folder, including imports/originals and backups.
- Review imported files before sharing them; they may contain private information.
- Standard library only; no third-party packages required.
'''

def main():
    setup()
    actions={
        "1":("Add memory",add_memory),
        "2":("List memories",list_memories),
        "3":("View memory",view_memory),
        "4":("Search memories",search_memory),
        "5":("Edit memory",edit_memory),
        "6":("Delete memory (backup first)",delete_memory),
        "7":("Import transcript text",import_transcript),
        "8":("List transcript archive",list_transcripts),
        "9":("Create backup now",lambda:print("Backup:",backup())),
        "10":("Restore backup",restore_backup),
        "11":("Show Sister registry",show_sisters),
        "12":("Import ChatGPT conversations.json export",import_chatgpt_export),
        "0":("Exit",None),
    }
    print(f"\nLUNA OS — FIRST LIGHT MEMORY ENGINE v{VERSION}\nPortable • Local-first • Inspectable • Standard library only")
    while True:
        print("\n"+"\n".join(f"{k}. {v[0]}" for k,v in actions.items()))
        try: choice=input("\nChoose: ").strip()
        except (EOFError,KeyboardInterrupt): print("\nClosed; local files remain saved."); break
        if choice=="0": print("Closed; local files remain saved."); break
        if choice not in actions: print("Choose a listed option."); continue
        try: actions[choice][1]()
        except (OSError,ValueError,zipfile.BadZipFile) as e: print(f"Operation failed safely: {e}")

if __name__=="__main__": main()
