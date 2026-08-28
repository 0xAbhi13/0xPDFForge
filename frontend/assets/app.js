// 0xPDFForge — Frontend SPA
const API = ""; // same origin

const DEFAULT_SECTIONS = [
  {id:"cover", title:"Cover", subtitle:"Title & meta", enabled:true},
  {id:"executive", title:"Executive Summary", subtitle:"High-level overview", enabled:true},
  {id:"overview", title:"Project Overview", subtitle:"Name, purpose, vital stats", enabled:true},
  {id:"goals", title:"Project Goals", subtitle:"Inferred purpose", enabled:true},
  {id:"stack", title:"Technology Stack", subtitle:"Frameworks & languages", enabled:true},
  {id:"statistics", title:"Project Statistics", subtitle:"Measured metrics", enabled:true},
  {id:"architecture", title:"Architecture", subtitle:"Inferred diagram", enabled:true},
  {id:"structure", title:"Project Structure", subtitle:"File tree", enabled:true},
  {id:"features", title:"Features", subtitle:"UI & functional signals", enabled:true},
  {id:"uipreview", title:"UI / Website Preview", subtitle:"Live or static", enabled:true},
  {id:"dependencies", title:"Dependencies", subtitle:"Manifests", enabled:true},
  {id:"api", title:"API Integration", subtitle:"Network calls", enabled:true},
  {id:"database", title:"Database", subtitle:"Only if evidence", enabled:true},
  {id:"security", title:"Security Findings", subtitle:"Static scan", enabled:true},
  {id:"testing", title:"Testing", subtitle:"Tests & frameworks", enabled:true},
  {id:"setup", title:"Development Setup", subtitle:"Run locally", enabled:true},
  {id:"usage", title:"Usage", subtitle:"How to use", enabled:true},
  {id:"limitations", title:"Limitations", subtitle:"Honest gaps", enabled:true},
  {id:"future", title:"Future Improvements", subtitle:"Suggestions", enabled:true},
  {id:"conclusion", title:"Conclusion", subtitle:"Wrap-up", enabled:true},
];

let state = {
  view: "landing",
  templates: [],
  filtered: [],
  selectedTemplate: "github",
  project: null,
  jobId: null,
  sections: JSON.parse(JSON.stringify(DEFAULT_SECTIONS)),
  pageSize: "A4",
};

const app = {
  async init(){
    await this.loadTemplates();
    this.renderTemplates();
    this.bindEvents();
    this.renderEditorSections();
    this.renderPreview();
    this.renderTemplateListForEditor();
    // health check for template count
    try{
      const r=await fetch(`${API}/api/health`);
      const j=await r.json();
      if(j.templates) document.getElementById("template-count").textContent=j.templates;
    }catch{}
  },

  async loadTemplates(){
    try{
      const r=await fetch(`${API}/api/templates`);
      const j=await r.json();
      state.templates=j.templates||[];
    }catch(e){
      state.templates=[];
    }
    if(state.templates.length===0){
      // fallback minimal
      state.templates=[
        {id:"github", name:"GitHub", category:"Developer", description:"Clean repo-style", preview_colors:["#0d1117","#58a6ff","#ffffff"], colors:{primary:"#0969DA"}},
        {id:"terminal", name:"Terminal", category:"Developer", description:"Monospace", preview_colors:["#0a0a0a","#00ff88","#1a1a1a"], colors:{primary:"#00FF88"}},
      ];
    }
    state.filtered=[...state.templates];
  },

  renderTemplates(){
    const grid=document.getElementById("template-grid");
    const grid2=document.getElementById("template-grid2");
    const html=(tpls)=> tpls.map(t=>`
      <div class="template-card bg-white border ${state.selectedTemplate===t.id?'border-ink ring-2 ring-ink':'border-line'} rounded-2xl overflow-hidden cursor-pointer" data-id="${t.id}" onclick="app.selectTemplate('${t.id}')">
        <div class="h-[118px] relative overflow-hidden" style="background:${t.preview_colors[0]}">
          <div class="absolute inset-0 opacity-90" style="background: linear-gradient(135deg, ${t.preview_colors[0]} 0%, ${t.preview_colors[1]} 55%, ${t.preview_colors[2]} 100%);"></div>
          <div class="absolute top-3 left-3 bg-white/95 backdrop-blur px-2.5 py-1 rounded-full text-[10px] font-bold tracking-widest">${t.category.toUpperCase()}</div>
          ${state.selectedTemplate===t.id?'<div class="absolute top-3 right-3 w-6 h-6 rounded-full bg-ink text-white grid place-items-center text-[10px]">✓</div>':''}
          <div class="absolute bottom-3 left-3 right-3 bg-white/95 backdrop-blur rounded-xl p-2.5">
            <div class="text-[11px] font-bold tracking-tight">${t.name}</div>
            <div class="text-[11px] text-muted leading-3 line-clamp-1">${t.description}</div>
          </div>
        </div>
        <div class="p-3 flex items-center justify-between">
          <span class="text-[11px] font-mono text-muted">${t.id}</span>
          <span class="text-[11px] font-medium ${state.selectedTemplate===t.id?'text-ink':'text-muted'}">${state.selectedTemplate===t.id?'Selected':'Select →'}</span>
        </div>
      </div>
    `).join("");
    if(grid) grid.innerHTML=html(state.filtered);
    if(grid2) grid2.innerHTML=html(state.filtered.slice(0, state.filtered.length)); // same
    document.getElementById("sel-tpl-name").textContent=(state.templates.find(x=>x.id===state.selectedTemplate)?.name||state.selectedTemplate);
    document.getElementById("editor-tpl-badge").textContent=`${state.templates.find(x=>x.id===state.selectedTemplate)?.name||state.selectedTemplate} • ${state.pageSize}`;
    this.updateColorPreview();
  },

  renderTemplateListForEditor(){
    const c=document.getElementById("editor-template-list");
    if(!c) return;
    c.innerHTML=state.templates.slice(0,16).map(t=>`
      <button onclick="app.selectTemplate('${t.id}')" class="text-left p-2 rounded-xl border ${state.selectedTemplate===t.id?'border-ink bg-[#f8fafc]':'border-line bg-white'} hover:border-ink">
        <div class="w-full h-8 rounded-lg" style="background: linear-gradient(90deg, ${t.preview_colors[0]}, ${t.preview_colors[1]})"></div>
        <div class="text-[11px] font-semibold mt-1">${t.name}</div>
        <div class="text-[10px] text-muted">${t.category}</div>
      </button>
    `).join("");
  },

  updateColorPreview(){
    const t=state.templates.find(x=>x.id===state.selectedTemplate);
    if(!t) return;
    document.getElementById("color-preview-primary").style.background=t.preview_colors[1]||t.colors.primary;
    document.getElementById("color-preview-accent").style.background=t.preview_colors[2]||t.colors.accent||"#fff";
  },

  selectTemplate(id){
    state.selectedTemplate=id;
    this.renderTemplates();
    this.renderTemplateListForEditor();
    this.renderPreview();
    this.toast(`Template: ${id}`);
  },

  show(view){
    state.view=view;
    ["landing","upload","analysis","results","templates","editor"].forEach(v=>{
      const el=document.getElementById(`view-${v}`);
      if(!el) return;
      if(v===view) el.classList.remove("hidden");
      else el.classList.add("hidden");
    });
    if(view==="landing"){
      document.getElementById("view-landing").classList.remove("hidden");
      window.scrollTo({top:0, behavior:"smooth"});
    }
    if(view==="results") window.scrollTo({top:0});
    if(view==="editor"){
      document.getElementById("view-editor").classList.remove("hidden");
      document.getElementById("view-editor").classList.add("flex");
    } else {
      const ed=document.getElementById("view-editor");
      if(ed) {ed.classList.add("hidden"); ed.classList.remove("flex");}
    }
    // nav visibility?
  },

  scrollTo(id){
    document.getElementById(id)?.scrollIntoView({behavior:"smooth"});
  },

  openUpload(){
    document.getElementById("view-upload").classList.remove("hidden");
    document.body.style.overflow="hidden";
  },
  closeUpload(){
    document.getElementById("view-upload").classList.add("hidden");
    document.body.style.overflow="";
  },

  bindEvents(){
    // template filter
    document.querySelectorAll(".filter-btn").forEach(b=>{
      b.addEventListener("click",()=>{
        document.querySelectorAll(".filter-btn").forEach(x=>{x.classList.remove("active","bg-ink","text-white"); x.classList.add("text-muted")});
        b.classList.add("active","bg-ink","text-white"); b.classList.remove("text-muted");
        const f=b.dataset.filter;
        this.filterTemplates(f, document.getElementById("template-search").value);
      });
    });
    document.querySelectorAll(".filter2-btn").forEach(b=>{
      b.addEventListener("click",()=>{
        document.querySelectorAll(".filter2-btn").forEach(x=>{x.classList.remove("active","bg-ink","text-white"); x.classList.add("text-muted")});
        b.classList.add("active","bg-ink","text-white"); b.classList.remove("text-muted");
        const f=b.dataset.filter2;
        this.filterTemplates(f, document.getElementById("template-search2").value);
        this.renderTemplates();
      });
    });
    document.getElementById("template-search")?.addEventListener("input",(e)=> this.filterTemplates(document.querySelector(".filter-btn.active")?.dataset.filter||"all", e.target.value));
    document.getElementById("template-search2")?.addEventListener("input",(e)=> {
      const f=document.querySelector(".filter2-btn.active")?.dataset.filter2||"all";
      this.filterTemplates(f, e.target.value);
      this.renderTemplates();
    });

    // dropzone
    const dz=document.getElementById("dropzone");
    const fi=document.getElementById("file-input");
    const browse=document.getElementById("browse-btn");
    browse?.addEventListener("click",(e)=>{e.stopPropagation(); fi.click()});
    dz?.addEventListener("click",()=> fi.click());
    dz?.addEventListener("dragover",(e)=>{e.preventDefault(); dz.classList.add("drop-active")});
    dz?.addEventListener("dragleave",()=> dz.classList.remove("drop-active"));
    dz?.addEventListener("drop",(e)=>{e.preventDefault(); dz.classList.remove("drop-active"); if(e.dataTransfer.files.length) this.handleFile(e.dataTransfer.files[0])});
    fi?.addEventListener("change",(e)=>{ if(e.target.files.length) this.handleFile(e.target.files[0])});

    document.getElementById("analyze-btn")?.addEventListener("click",()=> this.uploadAndAnalyze());
    document.getElementById("editor-pagesize")?.addEventListener("change",(e)=>{state.pageSize=e.target.value; document.getElementById("editor-tpl-badge").textContent=`${state.templates.find(x=>x.id===state.selectedTemplate)?.name} • ${state.pageSize}`; this.renderPreview()});
    document.getElementById("preview-zoom")?.addEventListener("change",(e)=>{
      const v=e.target.value.replace("%","");
      const sc=parseInt(v)/100;
      document.getElementById("preview-pages-container").style.transform=`scale(${sc})`;
      document.getElementById("preview-pages-container").style.transformOrigin="top center";
    });
    // drag for sections setup via delegation
  },

  filterTemplates(cat, q){
    let out=[...state.templates];
    if(cat && cat!=="all") out=out.filter(t=> t.category===cat);
    if(q) {
      const qq=q.toLowerCase();
      out=out.filter(t=> t.name.toLowerCase().includes(qq) || t.description.toLowerCase().includes(qq) || t.id.includes(qq));
    }
    state.filtered=out;
    this.renderTemplates();
  },

  handleFile(file){
    if(!file.name.toLowerCase().endsWith(".zip")){
      this.showError("Only .zip files are accepted.");
      return;
    }
    if(file.size> 55*1024*1024){
      this.showError("ZIP exceeds 50 MB limit.");
      return;
    }
    state.pendingFile=file;
    document.getElementById("file-info").classList.remove("hidden");
    document.getElementById("file-name").textContent=file.name;
    document.getElementById("file-size").textContent=`${(file.size/1024/1024).toFixed(2)} MB • ${file.type||"application/zip"}`;
    document.getElementById("analyze-btn").disabled=false;
    document.getElementById("upload-error").classList.add("hidden");
  },

  showError(msg){
    const el=document.getElementById("upload-error");
    el.textContent=msg; el.classList.remove("hidden");
  },

  async uploadAndAnalyze(){
    if(!state.pendingFile) return;
    const btn=document.getElementById("analyze-btn");
    btn.disabled=true; btn.textContent="Uploading…";
    document.getElementById("upload-progress").classList.remove("hidden");
    const fd=new FormData();
    fd.append("file", state.pendingFile);
    // Simulate progress bar for upload
    let prog=0;
    const iv=setInterval(()=>{
      prog=Math.min(92, prog+Math.random()*14);
      document.getElementById("progress-bar").style.width=prog+"%";
      document.getElementById("progress-text").textContent=`Uploading… ${Math.round(prog)}%`;
    },220);

    try{
      const r=await fetch(`${API}/api/upload`, {method:"POST", body: fd});
      clearInterval(iv);
      document.getElementById("progress-bar").style.width="100%";
      document.getElementById("progress-text").textContent="Analyzing…";
      if(!r.ok){
        const j=await r.json().catch(()=>({detail: r.statusText}));
        throw new Error(j.detail||"Upload failed");
      }
      const j=await r.json();
      state.jobId=j.job_id;
      state.project=j.project;
      try{ const hist=JSON.parse(localStorage.getItem('pdfforge_history')||'[]'); hist.unshift({name:j.project.project_name, jobId:j.job_id, at:new Date().toISOString(), files:j.project.statistics.total_files}); localStorage.setItem('pdfforge_history', JSON.stringify(hist.slice(0,6))); }catch(e){}
      // close upload, show analysis then results
      this.closeUpload();
      await this.showAnalysisThenResults(j.project);
    }catch(e){
      clearInterval(iv);
      document.getElementById("progress-bar").style.width="0%";
      btn.disabled=false; btn.textContent="Analyze Project →";
      this.showError(e.message);
    }
  },

  async showAnalysisThenResults(project){
    // Show analysis view with animated steps
    this.show("analysis");
    const steps=[
      "Files discovered","Languages detected","Frameworks detected","Dependencies analyzed","Architecture analyzed","Features detected","Security scan","Documentation generated"
    ];
    const container=document.getElementById("analysis-steps");
    container.innerHTML=steps.map((s,i)=>`
      <div class="flex items-center gap-3 p-3 rounded-xl border border-line bg-[#f8fafc]" id="step-${i}">
        <span class="progress-dot w-7 h-7 rounded-full border-2 border-line grid place-items-center text-[11px] bg-white" id="dot-${i}">○</span>
        <span class="text-[13px] font-medium flex-1">${s}</span>
        <span class="text-[11px] font-mono text-muted" id="step-status-${i}">pending</span>
      </div>
    `).join("");
    let pct=0;
    for(let i=0;i<steps.length;i++){
      const bar=document.getElementById("analysis-bar");
      const foot=document.getElementById("analysis-foot");
      // mark current as active
      const dot=document.getElementById(`dot-${i}`);
      dot.classList.add("border-ink","bg-ink","text-white"); dot.textContent="◐";
      document.getElementById(`step-status-${i}`).textContent="running…";
      foot.textContent=steps[i]+"…";
      bar.style.width=((i/steps.length)*100)+"%";
      await new Promise(r=>setTimeout(r, 280+ Math.random()*320));
      dot.textContent="✓"; dot.classList.remove("border-line"); dot.classList.add("bg-emerald-500","border-emerald-500","text-white");
      document.getElementById(`step-status-${i}`).textContent="done";
      document.getElementById(`step-${i}`).classList.add("bg-white");
      pct=((i+1)/steps.length)*100;
      bar.style.width=pct+"%";
    }
    document.getElementById("analysis-foot").textContent=`Completed in ${project.analysis_duration_ms} ms • ${project.statistics.total_files} files`;
    await new Promise(r=>setTimeout(r, 500));
    this.renderResults(project);
    this.show("results");
  },

  renderResults(p){
    state.project=p;
    document.getElementById("res-title").textContent=p.project_name;
    document.getElementById("res-subtitle").textContent=`Analyzed ${p.analyzed_at.slice(0,10)} • ${p.analysis_duration_ms} ms • ${p.metadata?.architecture?.type||p.architecture?.type||"project"}`;
    // frameworks
    const fwC=document.getElementById("res-frameworks");
    if(!p.frameworks || p.frameworks.length===0){
      fwC.innerHTML=`<span class="px-2.5 py-1 rounded-full bg-[#f1f5f9] border border-line text-[11px]">No frameworks confirmed — vanilla or undetected</span>`;
    } else {
      fwC.innerHTML=p.frameworks.map(f=>`
        <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-[11px] font-medium ${f.confidence==='confirmed'?'bg-ink text-white border-ink': f.confidence==='detected'?'bg-white border-line':'bg-amber-50 border-amber-200 text-amber-800'}">
          ${f.name} <span class="text-[10px] opacity-60">${f.confidence}</span>
        </span>
      `).join("");
    }
    document.getElementById("res-stack-count").textContent=`${p.frameworks.length} frameworks • ${p.languages.length} languages`;

    // languages
    const langC=document.getElementById("res-languages");
    langC.innerHTML=(p.languages||[]).slice(0,6).map(l=>`
      <div class="flex items-center gap-3">
        <div class="flex-1 h-2 rounded-full bg-[#f1f5f9] border border-line overflow-hidden"><div class="h-full bg-ink" style="width:${l.percentage}%"></div></div>
        <span class="text-[12px] font-medium w-[90px]">${l.language}</span>
        <span class="text-[11px] text-muted w-[50px] text-right">${l.percentage}%</span>
        <span class="text-[11px] text-muted">${l.files} files • ${l.loc} LOC</span>
      </div>
    `).join("") || `<span class="text-[12px] text-muted">No languages detected</span>`;

    // stats
    const s=p.statistics;
    document.getElementById("res-stats").innerHTML=`
      <div class="rounded-xl bg-ink text-white p-3"><div class="text-[11px] tracking-widest opacity-60">TOTAL FILES</div><div class="font-bold text-[20px]">${s.total_files}</div><div class="text-[11px] opacity-60">${s.source_files} source</div></div>
      <div class="rounded-xl bg-white border border-line p-3"><div class="text-[11px] tracking-widest text-muted">LOC</div><div class="font-bold text-[20px]">${s.total_loc}</div><div class="text-[11px] text-muted">${s.total_bytes>1024? (s.total_bytes/1024).toFixed(1)+' KB': s.total_bytes+' B'}</div></div>
      <div class="rounded-xl bg-white border border-line p-3"><div class="text-[11px] tracking-widest text-muted">DEPENDENCIES</div><div class="font-bold text-[20px]">${s.dependencies_count}</div><div class="text-[11px] text-muted">${s.frameworks_count} frameworks</div></div>
      <div class="rounded-xl bg-[#ffea00] p-3 border border-line"><div class="text-[11px] tracking-widest">IMAGES</div><div class="font-bold text-[20px]">${s.image_count}</div><div class="text-[11px] opacity-70">${s.assets_count} assets</div></div>
    `;
    document.getElementById("res-largest").innerHTML=(s.largest_files||[]).slice(0,5).map(f=>`<div class="flex justify-between gap-2"><span class="truncate">${f.path}</span><span class="text-muted">${(f.size/1024).toFixed(1)} KB</span></div>`).join("")||`<span class="text-muted">—</span>`;
    const scripts = s.build_scripts||{};
    document.getElementById("res-scripts").innerHTML=Object.keys(scripts).length? Object.entries(scripts).slice(0,5).map(([k,v])=>`<div><b>${k}</b>: <span class="font-mono text-[11px]">${v.slice(0,60)}</span></div>`).join("") : `<span class="text-muted">No build scripts detected</span>`;

    // features
    const fC=document.getElementById("res-features");
    if(!p.features || p.features.length===0){
      fC.innerHTML=`<div class="col-span-2 text-[12px] text-muted p-3 bg-[#f8fafc] border border-line rounded-xl"><i>No distinct UI features confirmed. Project may be non-UI.</i></div>`;
    } else {
      fC.innerHTML=p.features.slice(0,12).map(f=>`
        <div class="flex items-start gap-2 p-2.5 rounded-xl border ${f.confidence==='detected'?'border-line bg-white':'border-amber-200 bg-amber-50'}">
          <span class="mt-0.5 w-5 h-5 rounded-full grid place-items-center text-[10px] ${f.confidence==='detected'?'bg-emerald-500 text-white':'bg-amber-500 text-white'}">✓</span>
          <div><div class="text-[12px] font-semibold">${f.name} <span class="text-[10px] font-normal px-1.5 py-0.5 rounded-full bg-white border border-line">${f.confidence}</span></div><div class="text-[11px] text-muted leading-3 mt-0.5">${(f.evidence[0]||'').slice(0,80)}</div></div>
        </div>
      `).join("");
    }
    const wd=p.metadata?.website_details||{};
    document.getElementById("res-website").innerHTML=`<span class="inline-flex gap-2 flex-wrap"><span class="px-2 py-1 rounded-full bg-white border border-line">${wd.media_queries||0} media queries</span><span class="px-2 py-1 rounded-full bg-white border border-line">${wd.event_listeners||0} listeners</span><span class="px-2 py-1 rounded-full bg-white border border-line">${wd.forms||0} forms</span><span class="px-2 py-1 rounded-full ${wd.has_responsive?'bg-emerald-50 border-emerald-200 text-emerald-700':'bg-white border-line'}">${wd.has_responsive?'Responsive':'Not responsive'}</span></span>`;

    // tree
    const tree=p.file_tree;
    function renderTree(node, prefix="", isLast=true, depth=0, lines=[]){
      if(depth===0) lines.push(node.name+"/");
      else {
        const conn=isLast?"└── ":"├── ";
        lines.push(prefix+conn+node.name+(node.type==="dir"?"/":`  (${(node.size/1024).toFixed(1)}KB)`));
      }
      if(node.children){
        const np=prefix+(isLast?"    ":"│   ");
        node.children.slice(0,30).forEach((c,i)=> renderTree(c, np, i===Math.min(29, node.children.length-1), depth+1, lines));
        if(node.children.length>30) lines.push(np+"└── ... +"+(node.children.length-30)+" more");
      }
      return lines;
    }
    let treeText="";
    if(tree) treeText=renderTree(tree).join("\n");
    else treeText=(p.flat_files||[]).slice(0,40).join("\n");
    document.getElementById("res-tree").textContent=treeText.slice(0,3000);

    // arch
    const arch=p.architecture||{};
    document.getElementById("res-arch-desc").textContent=arch.description||"No architecture inferred";
    document.getElementById("res-arch-type").textContent=(arch.type||"generic").toUpperCase();
    const diag=document.getElementById("res-arch-diag");
    diag.innerHTML=(arch.nodes||[]).map((n,i)=>`
      <div class="rounded-xl border border-line bg-[#f8fafc] p-2.5 text-center">
        <div class="text-[12px] font-bold">${n.label.replace(/\n/g," → ")}</div>
        <div class="text-[11px] text-muted">${n.kind}</div>
      </div>
      ${i<arch.nodes.length-1?`<div class="text-center text-ink font-bold">↓ <span class="text-[11px] font-normal text-muted">${(arch.edges[i]?.label||"")}</span></div>`:""}
    `).join("");

    // apis
    document.getElementById("res-api-count").textContent=`• ${p.apis.length} endpoints`;
    document.getElementById("res-apis").innerHTML=p.apis.length? p.apis.slice(0,8).map(a=>`
      <div class="flex items-center gap-2 p-2 rounded-xl border border-line bg-[#f8fafc]">
        <span class="px-1.5 py-1 rounded bg-ink text-white text-[10px] font-bold">${a.method}</span>
        <span class="font-mono text-[11px] truncate flex-1">${a.endpoint}</span>
        <span class="text-[11px] text-muted">${a.library}</span>
      </div>
    `).join("") : `<div class="text-[12px] text-muted p-2 bg-[#f8fafc] border border-line rounded-xl"><i>No API calls detected</i></div>`;

    // dbs
    document.getElementById("res-dbs").innerHTML=p.databases.length? p.databases.map(d=>`
      <div class="p-2.5 rounded-xl border ${d.confidence==='confirmed'?'border-ink bg-white':'border-line bg-[#f8fafc]'}">
        <div class="text-[12px] font-semibold">${d.technology} <span class="text-[10px] px-1.5 py-0.5 rounded-full border ${d.confidence==='confirmed'?'bg-emerald-500 text-white border-emerald-500': d.confidence==='detected'?'bg-white border-line':'bg-amber-100 border-amber-200'}">${d.confidence}</span></div>
        <div class="text-[11px] text-muted mt-1">${(d.evidence||[]).join(" • ").slice(0,90)}</div>
        <div class="text-[11px] font-mono text-muted">${(d.files||[]).join(", ").slice(0,60)}</div>
      </div>
    `).join("") : `<div class="text-[12px] text-muted p-2 bg-[#f8fafc] border border-line rounded-xl"><i>No database confirmed — checked connection code, models, schemas, SQL, ORM</i></div>`;

    // security
    document.getElementById("res-security").innerHTML=p.security.length? p.security.map(s=>`
      <div class="p-2.5 rounded-xl border ${s.severity==='high'?'border-red-200 bg-red-50':'border-amber-200 bg-amber-50'}">
        <div class="text-[12px] font-semibold"><span class="px-1.5 py-0.5 rounded text-white text-[10px] ${s.severity==='high'?'bg-red-600': s.severity==='medium'?'bg-amber-600':'bg-emerald-600'}">${s.severity.toUpperCase()}</span> ${s.title}</div>
        <div class="text-[11px] text-muted mt-1">${s.description.slice(0,160)}</div>
        <div class="text-[11px] font-mono mt-1">${s.file||''} ${s.evidence_snippet||''}</div>
      </div>
    `).join("") : `<div class="text-[12px] text-emerald-700 p-2 bg-emerald-50 border border-emerald-200 rounded-xl"><b>Static scan detected no obvious high-severity patterns.</b><br><span class="text-[11px] text-muted">Not a full audit — do not claim “secure”.</span></div>`;

    // docs
    const doc=p.documentation||{};
    document.getElementById("res-docs").innerHTML=`
      <div>README: <b>${doc.has_readme?'Found':'Not found'}</b></div>
      ${doc.readme_excerpt? `<div class="mt-1 p-2 bg-[#f8fafc] border border-line rounded-xl font-mono text-[11px] max-h-[120px] overflow-auto">${doc.readme_excerpt.slice(0,400).replace(/</g,"&lt;")}</div>`:""}
      <div class="mt-2 text-muted">${p.flat_files.length} files indexed • ${p.statistics.ignored_files} ignored (node_modules etc)</div>
      <div class="mt-1 text-win text-[11px]">${p.screenshots?.message||''}</div>
    `;
    document.getElementById("meta-title").textContent=p.project_name;
    this.renderEditorSections();
    this.renderPreview();
  },

  openTemplateGallery(){
    this.show("templates");
    this.renderTemplates();
  },

  openEditor(){
    if(!state.project){
      this.toast("Upload a project first");
      return;
    }
    this.show("editor");
    this.renderEditorSections();
    this.renderPreview();
    this.renderTemplateListForEditor();
  },

  renderEditorSections(){
    const c=document.getElementById("editor-sections");
    if(!c) return;
    c.innerHTML=state.sections.map((s,idx)=>`
      <div class="group flex items-center gap-2 p-2.5 rounded-xl border ${s.enabled?'bg-white border-line':'bg-[#f1f5f9] border-dashed border-line opacity-60'} hover:border-ink cursor-grab" draggable="true" data-idx="${idx}" ondragstart="app.dragStart(event)" ondragover="app.dragOver(event)" ondrop="app.drop(event)">
        <span class="cursor-grab text-muted">≡</span>
        <div class="flex-1 min-w-0">
          <div class="text-[12px] font-medium truncate ${!s.enabled?'line-through':''}">${String(idx+1).padStart(2,'0')} — ${s.title}</div>
          <div class="text-[11px] text-muted truncate">${s.subtitle}</div>
        </div>
        <label class="relative inline-flex items-center cursor-pointer">
          <input type="checkbox" ${s.enabled?'checked':''} onchange="app.toggleSection(${idx}, this.checked)" class="sr-only peer">
          <div class="w-9 h-5 bg-gray-200 rounded-full peer peer-checked:bg-ink transition"></div>
          <div class="absolute left-0.5 top-0.5 w-4 h-4 bg-white rounded-full transition peer-checked:translate-x-4"></div>
        </label>
        <button onclick="app.editSection(${idx})" class="w-7 h-7 rounded-full bg-white border border-line grid place-items-center text-[11px] hover:bg-gray-50">✎</button>
      </div>
    `).join("");
    document.getElementById("preview-pages").textContent=`${state.sections.filter(s=>s.enabled).length} sections`;
  },

  toggleSection(idx, val){
    state.sections[idx].enabled=val;
    this.renderEditorSections();
    this.renderPreview();
  },

  editSection(idx){
    const s=state.sections[idx];
    const nv=prompt(`Edit section "${s.title}" — content override (leave empty to use auto-generated):`, s.content_override||"");
    if(nv===null) return;
    s.content_override=nv.trim() || null;
    this.renderPreview();
    this.toast(`Section "${s.title}" updated`);
  },

  resetSections(){
    state.sections=JSON.parse(JSON.stringify(DEFAULT_SECTIONS));
    this.renderEditorSections();
    this.renderPreview();
  },

  addCustomSection(){
    const txt=document.getElementById("custom-text").value.trim();
    if(!txt) return this.toast("Enter text first");
    state.sections.push({id:"custom_"+Date.now(), title:"Custom Note", subtitle:"User added", enabled:true, content_override: txt});
    document.getElementById("custom-text").value="";
    this.renderEditorSections();
    this.renderPreview();
    this.toast("Custom section added");
  },

  dragStart(e){
    e.dataTransfer.setData("text/plain", e.currentTarget.dataset.idx);
    e.currentTarget.classList.add("drag-ghost");
  },
  dragOver(e){e.preventDefault()},
  drop(e){
    e.preventDefault();
    const from=parseInt(e.dataTransfer.getData("text/plain"));
    const to=parseInt(e.currentTarget.dataset.idx);
    if(isNaN(from)||isNaN(to)||from===to) return;
    const item=state.sections.splice(from,1)[0];
    state.sections.splice(to,0,item);
    this.renderEditorSections();
    this.renderPreview();
  },

  renderPreview(){
    const c=document.getElementById("preview-pages-container");
    if(!c || !state.project) {
      if(c) c.innerHTML=`<div class="bg-white rounded-2xl border border-line p-6 text-center text-muted text-[13px]">Upload a project to preview PDF</div>`;
      return;
    }
    const t=state.templates.find(x=>x.id===state.selectedTemplate)||state.templates[0];
    const enabled=state.sections.filter(s=>s.enabled);
    c.innerHTML=`
      <div class="bg-white rounded-[14px] border border-line shadow-sm overflow-hidden">
        <div class="h-[42px] flex items-center px-4 border-b" style="background:${t.colors.bg}; border-color:${t.colors.line}">
          <div class="text-[11px] font-mono" style="color:${t.colors.muted}">0xPDFForge • ${t.name} • ${state.pageSize}</div>
          <span class="ml-auto w-2 h-2 rounded-full" style="background:${t.colors.primary}"></span>
        </div>
        <div class="p-6">
          <div class="text-[11px] tracking-[0.14em]" style="color:${t.colors.muted}">COVER</div>
          <h1 class="font-bold text-[18px] mt-1" style="color:${t.colors.primary}">${state.project.project_name}</h1>
          <p class="text-[11px] mt-1" style="color:${t.colors.muted}">${state.project.architecture?.description?.slice(0,140)||'Deterministic documentation • '+ state.project.statistics.total_files +' files'}</p>
          <div class="mt-3 grid grid-cols-3 gap-2">
            <div class="rounded-xl p-2 text-center text-white" style="background:${t.colors.primary}"><div class="text-[14px] font-bold">${state.project.statistics.total_files}</div><div class="text-[10px] opacity-80">files</div></div>
            <div class="rounded-xl p-2 text-center border" style="background:${t.colors.card}; border-color:${t.colors.line}"><div class="text-[14px] font-bold" style="color:${t.colors.text}">${state.project.languages.length}</div><div class="text-[10px]" style="color:${t.colors.muted}">languages</div></div>
            <div class="rounded-xl p-2 text-center border" style="background:${t.colors.card}; border-color:${t.colors.line}"><div class="text-[14px] font-bold" style="color:${t.colors.text}">${state.project.frameworks.length}</div><div class="text-[10px]" style="color:${t.colors.muted}">frameworks</div></div>
          </div>
        </div>
      </div>
      ${enabled.slice(0,8).map(s=>`
        <div class="bg-white rounded-[14px] border border-line shadow-sm p-5">
          <div class="flex items-center gap-2">
            <span class="w-1.5 h-8 rounded-full" style="background:${t.colors.primary}"></span>
            <div>
              <div class="font-semibold text-[12px]" style="color:${t.colors.primary}">${s.title.toUpperCase()}</div>
              <div class="text-[11px]" style="color:${t.colors.muted}">${s.subtitle}</div>
            </div>
            <span class="ml-auto text-[10px] px-1.5 py-0.5 rounded-full border" style="border-color:${t.colors.line}; color:${t.colors.muted}">${s.id}</span>
          </div>
          <div class="mt-3 text-[11px] leading-4" style="color:${t.colors.text}">
            ${s.content_override? s.content_override.slice(0,220).replace(/\n/g,"<br>") : `<span style="color:${t.colors.muted}"><i>Auto-generated from evidence — deterministic, no hallucination. This section will be rendered in <b>${t.name}</b> style with ${t.fonts.heading} headings and consistent spacing.</i></span>`}
          </div>
        </div>
      `).join("")}
      ${enabled.length>8?`<div class="text-center text-[11px] text-muted">+${enabled.length-8} more sections in full PDF…</div>`:""}
      <div class="text-center text-[11px] font-mono text-muted">— ${enabled.length} sections • A4 • Page numbers • Redacted secrets —</div>
    `;
  },

  async generatePDF(){
    if(!state.project || !state.jobId) return this.toast("No project");
    const btn=document.getElementById("generate-btn");
    const spinner=document.getElementById("gen-spinner");
    btn.disabled=true; spinner.classList.remove("hidden"); btn.childNodes[btn.childNodes.length-1].textContent=" Generating…";
    try{
      const body={
        job_id: state.jobId,
        template_id: state.selectedTemplate,
        page_size: state.pageSize,
        sections: state.sections,
        project_override: null
      };
      const r=await fetch(`${API}/api/generate`, {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify(body)});
      if(!r.ok){
        const j=await r.json().catch(()=>({detail:r.statusText}));
        throw new Error(j.detail||"PDF generation failed");
      }
      const blob=await r.blob();
      const url=URL.createObjectURL(blob);
      const a=document.createElement("a");
      a.href=url;
      const safeName = (state.project.project_name || 'project').replace(/[^A-Za-z0-9._-]/g, '_').substring(0,80) || 'project';
      a.download=`${safeName}_${state.selectedTemplate}_${state.pageSize}.pdf`;
      document.body.appendChild(a); a.click(); a.remove();
      URL.revokeObjectURL(url);
      this.toast("PDF downloaded ✓");
    }catch(e){
      this.toast("Error: "+e.message);
    }finally{
      btn.disabled=false; spinner.classList.add("hidden"); btn.innerHTML=`<span id="gen-spinner" class="hidden w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span> Generate PDF`;
      document.getElementById("gen-spinner").classList.add("hidden");
    }
  },

  async loadSample(){
    this.toast("Loading sample project…");
    try{
      const r = await fetch('/examples/sample-project.zip');
      if(!r.ok) throw new Error('Sample not found');
      const blob = await r.blob();
      const file = new File([blob], 'sample-project.zip', {type:'application/zip'});
      this.handleFile(file);
      this.openUpload();
      // auto-analyze after short delay to show flow
      setTimeout(()=>{ if(state.pendingFile) this.uploadAndAnalyze(); }, 600);
    }catch(e){
      this.toast("Create a sample ZIP from examples/sample-project and upload it");
      this.openUpload();
    }
  },

  toast(msg){
    const t=document.getElementById("toast");
    t.textContent=msg; t.classList.remove("hidden");
    setTimeout(()=> t.classList.add("hidden"), 2600);
  }
};

document.addEventListener("DOMContentLoaded",()=> app.init());
