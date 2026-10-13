"use strict";
const byId = (id) => document.getElementById(id);
const form = byId("triage-form");
const runButton = byId("run");
let py = null;
let lastJSON = "";
function num(id) {
  const el = byId(id);
  if (el.value.trim() === "") return null;
  const value = Number(el.value);
  if (!Number.isFinite(value) || value < 0) throw new Error("Enter a finite non-negative number for " + id);
  return value;
}
function needed(id) {
  const value = num(id);
  if (value === null) throw new Error("Enter a value for " + id);
  return value;
}
const checked = (id) => byId(id).checked;
function makeRequest() {
  const mode = byId("mode").value;
  if (mode === "bdg") return ["interpret_bdg", {value_pg_ml:needed("bdg")}];
  if (mode === "gm") return ["interpret_gm", {index_value:needed("gm"),specimen_type:byId("specimen").value}];
  if (mode === "crag") return ["interpret_crag", {positive:checked("crag-positive"),titer:byId("titer").value||null,specimen_type:byId("crag-specimen").value}];
  if (mode === "mannan") {
    const a = {mannan_value:num("mannan"),anti_mannan_value:num("anti-mannan")};
    if (a.mannan_value === null && a.anti_mannan_value === null) throw new Error("Enter a mannan measurement.");
    return ["interpret_mannan",a];
  }
  if (mode !== "combined") throw new Error("Invalid assay selection.");
  const args = {
    bdg_value:num("bdg"),gm_index:num("gm"),gm_specimen:byId("specimen").value,
    crag_positive:checked("crag-tested") ? checked("crag-positive") : null,
    mannan_value:num("mannan"),anti_mannan_value:num("anti-mannan")
  };
  const factors = {};
  for (const key of ["neutropenic","hematologic_malignancy","prolonged_icu","corticosteroids"]) {
    if (checked(key)) factors[key]=true;
  }
  if (Object.keys(factors).length) args.host_factors=factors;
  if ([args.bdg_value,args.gm_index,args.crag_positive,args.mannan_value,args.anti_mannan_value].every(x=>x===null))
    throw new Error("Supply at least one assay result.");
  return ["combined_interpretation",args];
}
form.addEventListener("submit",event=>{
  event.preventDefault();
  if (!py) return;
  try {
    const [name,args] = makeRequest();
    py.globals.set("request_json",JSON.stringify(args));
    // The Python function is chosen from fixed local names, not arbitrary user text.
    const json = py.runPython(
      "import json\nfrom myco_sentinel import "+name+"\n"+
      "_result = "+name+"(**json.loads(request_json))\njson.dumps(_result, allow_nan=False)"
    );
    const result = JSON.parse(json);
    lastJSON = JSON.stringify(result,null,2);
    byId("output").textContent = lastJSON;
    byId("error").textContent = result.error ? JSON.stringify(result.error) : "";
    byId("summary").textContent = result.error ? "Invalid input; no interpretation issued." :
      (result.combined_interpretation || result.interpretation || "Evaluation complete.");
    byId("copy").disabled = false;
    byId("download").disabled = false;
  } catch(e) {
    byId("summary").textContent="No interpretation issued.";
    byId("error").textContent=String(e instanceof Error ? e.message : e);
  }
});
byId("copy").addEventListener("click",async()=>{
  try { await navigator.clipboard.writeText(lastJSON); byId("status").textContent="JSON copied."; }
  catch { byId("status").textContent="Clipboard unavailable; select and copy the JSON manually."; }
});
byId("download").addEventListener("click",()=>{
  if (!lastJSON) return;
  const url = URL.createObjectURL(new Blob([lastJSON+"\n"],{type:"application/json"}));
  const a = document.createElement("a");
  a.href=url; a.download="fungal-antigen-interpretation.json";
  document.body.appendChild(a); a.click(); a.remove();
  URL.revokeObjectURL(url);
});
(async()=>{
  try {
    if(typeof loadPyodide!=="function") throw new Error("Pyodide could not be loaded.");
    py=await loadPyodide({indexURL:"https://cdn.jsdelivr.net/pyodide/v0.27.7/full/"});
    const response=await fetch("../myco_sentinel.py");
    if(!response.ok) throw new Error("Python source unavailable ("+response.status+").");
    py.FS.writeFile("/home/pyodide/myco_sentinel.py",await response.text());
    py.runPython("import sys\nsys.path.insert(0,'/home/pyodide')\nimport myco_sentinel");
    runButton.disabled=false;
    byId("status").textContent="Python ready · Local execution";
    byId("summary").textContent="Select assay results and run an interpretation.";
  } catch(e) {
    py=null;
    byId("status").textContent="Runtime unavailable";
    byId("error").textContent=String(e instanceof Error?e.message:e);
    byId("summary").textContent="The application could not start.";
  }
})();
