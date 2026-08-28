import os, re
from typing import List, Dict
from ..models import DBEvidence

DB_RULES = [
    {"tech":"SQLite", "patterns":[r"sqlite", r"\.db\b", r"\.sqlite", r"sqlite3"], "files":["*.db","*.sqlite","*.sqlite3","schema.sql"], "deps":["sqlite3","better-sqlite3"]},
    {"tech":"MySQL", "patterns":[r"mysql", r"mysqli", r"mysql2", r"create\s+table.*mysql"], "deps":["mysql","mysql2","pymysql"]},
    {"tech":"PostgreSQL", "patterns":[r"postgres", r"postgresql", r"pg\.", r"psycopg"], "deps":["pg","psycopg2","psycopg","postgres"]},
    {"tech":"MongoDB", "patterns":[r"mongodb", r"mongoose", r"MongoClient"], "deps":["mongodb","mongoose"]},
    {"tech":"Redis", "patterns":[r"redis", r"createClient.*redis"], "deps":["redis","ioredis"]},
    {"tech":"Supabase", "patterns":[r"supabase", r"createClient.*supabase"], "deps":["@supabase/supabase-js"]},
    {"tech":"Firebase", "patterns":[r"firebase", r"firestore", r"initializeApp.*firebase"], "deps":["firebase"]},
    {"tech":"Prisma", "patterns":[r"prisma", r"@prisma/client"], "deps":["prisma","@prisma/client"]},
    {"tech":"Sequelize", "patterns":[r"sequelize"], "deps":["sequelize"]},
    {"tech":"TypeORM", "patterns":[r"typeorm"], "deps":["typeorm"]},
    {"tech":"Mongoose", "patterns":[r"mongoose"], "deps":["mongoose"]},
    {"tech":"SQLAlchemy", "patterns":[r"sqlalchemy"], "deps":["sqlalchemy"]},
]

def detect_databases(root: str, files: List[str], deps_names: List[str]=None) -> List[DBEvidence]:
    deps_names = [d.lower() for d in (deps_names or [])]
    basenames=[os.path.basename(f).lower() for f in files]
    rels=[os.path.relpath(f,root).lower() for f in files]
    # Collect file contents for patterns (sample)
    sample=[f for f in files if os.path.splitext(f)[1].lower() in [".js",".ts",".py",".php",".java",".sql",".json",".env.example"]][:60]
    blob=""
    file_hits: Dict[str, List[str]]={}
    for f in sample:
        try:
            if os.path.getsize(f) > 600*1024:
                continue
            with open(f,'r',encoding='utf-8',errors='ignore') as fh:
                txt=fh.read(8000).lower()
                blob+=txt+"\n"
                # track hits per db
                for rule in DB_RULES:
                    for pat in rule["patterns"]:
                        if re.search(pat.lower(), txt):
                            file_hits.setdefault(rule["tech"], []).append(os.path.relpath(f,root))
        except:
            continue
    blob_lower=blob.lower()
    results: List[DBEvidence]=[]
    for rule in DB_RULES:
        tech=rule["tech"]
        evidences=[]
        files_evidence=list(dict.fromkeys(file_hits.get(tech, [])))[:3]
        # Check deps
        for dep in rule.get("deps",[]):
            if dep.lower() in deps_names:
                evidences.append(f"dependency:{dep}")
        # Check patterns in blob
        for pat in rule["patterns"]:
            if re.search(pat.lower(), blob_lower):
                evidences.append(f"pattern:{pat}")
                break
        # Check file names like schema.sql, .db
        for fn in rels:
            if tech.lower() in fn:
                evidences.append(f"file:{fn}")
                if fn not in files_evidence:
                    files_evidence.append(fn)
            if fn.endswith(".sql") and tech in ["MySQL","PostgreSQL","SQLite"]:
                # if sql file exists, consider evidence but not alone
                pass
        # SQL file special
        if any(fn.endswith(".sql") for fn in rels) and tech in ["MySQL","PostgreSQL","SQLite"]:
            # Check if sql contains create table
            if "create table" in blob_lower:
                if not evidences:
                    evidences.append("file:*.sql + CREATE TABLE")
                    files_evidence.extend([fn for fn in rels if fn.endswith(".sql")][:2])

        if evidences:
            evidences=list(dict.fromkeys(evidences))[:4]
            # Determine confidence
            if any(e.startswith("dependency") for e in evidences) and any(e.startswith("pattern") for e in evidences):
                conf="confirmed"
            elif any(e.startswith("dependency") for e in evidences):
                conf="detected"
            elif len(files_evidence)>=2:
                conf="detected"
            else:
                conf="inferred"
            results.append(DBEvidence(technology=tech, confidence=conf, evidence=evidences, files=files_evidence))
    # Sort confirmed first
    order={"confirmed":0,"detected":1,"inferred":2}
    results.sort(key=lambda x: (order.get(x.confidence,9), x.technology))
    return results
