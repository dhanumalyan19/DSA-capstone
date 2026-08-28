const els = {
  sourceText: document.querySelector("#sourceText"),
  decodedText: document.querySelector("#decodedText"),
  heroCanvas: document.querySelector("#heroCanvas"),
  enterStudioBtn: document.querySelector("#enterStudioBtn"),
  skipToStudioBtn: document.querySelector("#skipToStudioBtn"),
  studioApp: document.querySelector("#studioApp"),
  sampleSelect: document.querySelector("#sampleSelect"),
  loadSampleBtn: document.querySelector("#loadSampleBtn"),
  textFileInput: document.querySelector("#textFileInput"),
  huffFileInput: document.querySelector("#huffFileInput"),
  signalCanvas: document.querySelector("#signalCanvas"),
  pipelineProgress: document.querySelector("#pipelineProgress"),
  runBtn: document.querySelector("#runBtn"),
  clearBtn: document.querySelector("#clearBtn"),
  downloadCompressedBtn: document.querySelector("#downloadCompressedBtn"),
  exportReportBtn: document.querySelector("#exportReportBtn"),
  downloadTextBtn: document.querySelector("#downloadTextBtn"),
  decodeLastBtn: document.querySelector("#decodeLastBtn"),
  message: document.querySelector("#message"),
  sourceMetric: document.querySelector("#sourceMetric"),
  codesMetric: document.querySelector("#codesMetric"),
  storedMetric: document.querySelector("#storedMetric"),
  verifyMetric: document.querySelector("#verifyMetric"),
  originalSize: document.querySelector("#originalSize"),
  bitstreamSize: document.querySelector("#bitstreamSize"),
  ratioValue: document.querySelector("#ratioValue"),
  savingsValue: document.querySelector("#savingsValue"),
  bitPreview: document.querySelector("#bitPreview"),
  frequencyList: document.querySelector("#frequencyList"),
  sizeChart: document.querySelector("#sizeChart"),
  treeSvg: document.querySelector("#treeSvg"),
  zoomInBtn: document.querySelector("#zoomInBtn"),
  zoomOutBtn: document.querySelector("#zoomOutBtn"),
  zoomResetBtn: document.querySelector("#zoomResetBtn"),
  codeSearch: document.querySelector("#codeSearch"),
  codeTableBody: document.querySelector("#codeTableBody"),
  analysisList: document.querySelector("#analysisList"),
  entropyExplanation: document.querySelector("#entropyExplanation"),
  comparisonChart: document.querySelector("#comparisonChart"),
  prevStepBtn: document.querySelector("#prevStepBtn"),
  nextStepBtn: document.querySelector("#nextStepBtn"),
  stepCounter: document.querySelector("#stepCounter"),
  stepProgress: document.querySelector("#stepProgress"),
  stepText: document.querySelector("#stepText"),
};

const state = {
  result: null,
  codeRows: [],
  steps: [],
  stepIndex: 0,
  compressedBase64: "",
  lastSourceText: "",
  signalTick: 0,
  heroTick: 0,
  pipelineStage: 0,
  pointer: { x: 0.5, y: 0.5 },
  treeViewBox: null,
  treeBaseViewBox: null,
  treeDrag: null,
};

els.runBtn.addEventListener("click", runCompression);
els.enterStudioBtn.addEventListener("click", scrollToStudio);
els.skipToStudioBtn.addEventListener("click", scrollToStudio);
els.loadSampleBtn.addEventListener("click", loadSelectedSample);
els.clearBtn.addEventListener("click", clearAll);
els.downloadCompressedBtn.addEventListener("click", downloadCompressed);
els.exportReportBtn.addEventListener("click", exportReport);
els.downloadTextBtn.addEventListener("click", downloadDecodedText);
els.decodeLastBtn.addEventListener("click", decodeLastResult);
els.zoomInBtn.addEventListener("click", () => zoomTree(0.82));
els.zoomOutBtn.addEventListener("click", () => zoomTree(1.22));
els.zoomResetBtn.addEventListener("click", resetTreeView);
els.treeSvg.addEventListener("wheel", onTreeWheel, { passive: false });
els.treeSvg.addEventListener("pointerdown", startTreeDrag);
els.treeSvg.addEventListener("pointermove", moveTreeDrag);
els.treeSvg.addEventListener("pointerup", endTreeDrag);
els.treeSvg.addEventListener("pointerleave", endTreeDrag);
els.codeSearch.addEventListener("input", renderCodeTable);
els.prevStepBtn.addEventListener("click", () => moveStep(-1));
els.nextStepBtn.addEventListener("click", () => moveStep(1));
els.sourceText.addEventListener("input", updateInputMetric);
els.textFileInput.addEventListener("change", loadTextFile);
els.huffFileInput.addEventListener("change", loadHuffFile);

document.querySelectorAll(".tab").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((tab) => tab.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach((panel) => panel.classList.remove("active"));
    button.classList.add("active");
    document.querySelector(`#${button.dataset.tab}`).classList.add("active");
  });
});

updateEmptyState();
loadSamples();
resizeHeroCanvas();
resizeSignalCanvas();
requestAnimationFrame(drawHero);
requestAnimationFrame(drawSignal);
window.addEventListener("resize", () => {
  resizeHeroCanvas();
  resizeSignalCanvas();
});
window.addEventListener("pointermove", (event) => {
  state.pointer.x = event.clientX / Math.max(1, window.innerWidth);
  state.pointer.y = event.clientY / Math.max(1, window.innerHeight);
});

async function runCompression() {
  const text = els.sourceText.value;
  if (text.length === 0) {
    showMessage("Enter text before running the pipeline.", "error");
    return;
  }

  setBusy(true);
  setPipelineStage(2);
  showMessage("Running Huffman pipeline...");

  try {
    const response = await fetch("/api/compress", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Compression failed.");
    }

    state.result = data;
    state.codeRows = data.codeTable || [];
    state.steps = data.steps || [];
    state.stepIndex = 0;
    state.compressedBase64 = data.compressedBase64;
    state.lastSourceText = text;

    renderCompressionResult(data);
    setPipelineStage(5);
    showMessage("Compression complete. The .huff file is ready to download.", "good");
  } catch (error) {
    showMessage(error.message, "error");
  } finally {
    setBusy(false);
  }
}

function renderCompressionResult(data) {
  const summary = data.summary;

  els.sourceMetric.textContent = `${summary.characters} chars, ${summary.uniqueSymbols} unique`;
  els.codesMetric.textContent = `${state.codeRows.length} codes`;
  els.storedMetric.textContent = `${summary.storedBytes} bytes`;
  els.verifyMetric.textContent = "Not decoded";

  els.originalSize.textContent = `${summary.originalBytes} bytes`;
  els.bitstreamSize.textContent = `${summary.theoreticalBits} bits`;
  els.ratioValue.textContent = `${formatNumber(summary.compressionRatio)}:1`;
  els.savingsValue.textContent = `${formatNumber(summary.spaceSavingsPct)}%`;
  els.bitPreview.textContent = data.bitPreview || "(empty)";

  renderFrequencies(data.frequencies || []);
  renderSizeChart(data);
  renderTree(data.tree);
  renderCodeTable();
  renderAnalysis(data);
  renderComparison(data.comparison);
  renderStep();

  els.downloadCompressedBtn.disabled = false;
  els.exportReportBtn.disabled = false;
  els.decodeLastBtn.disabled = false;
}

function renderFrequencies(rows) {
  els.frequencyList.replaceChildren();
  if (!rows.length) {
    els.frequencyList.textContent = "No symbols yet.";
    return;
  }

  rows.slice(0, 24).forEach((row, index) => {
    const chip = document.createElement("div");
    chip.className = "frequency-chip";
    chip.style.animationDelay = `${Math.min(index * 18, 220)}ms`;
    chip.innerHTML = `<span>${escapeHtml(row.symbol)}</span><strong>${row.frequency}</strong>`;
    els.frequencyList.appendChild(chip);
  });
}

function renderCodeTable() {
  const needle = els.codeSearch.value.trim().toLowerCase();
  els.codeTableBody.replaceChildren();

  const rows = state.codeRows.filter((row) => {
    const value = `${row.symbol} ${row.frequency} ${row.probability} ${row.code}`.toLowerCase();
    return !needle || value.includes(needle);
  });

  if (!rows.length) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td colspan="5">No matching symbols.</td>`;
    els.codeTableBody.appendChild(tr);
    return;
  }

  rows.forEach((row) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${escapeHtml(row.symbol)}</td>
      <td>${row.frequency}</td>
      <td>${formatNumber(row.probability, 4)}</td>
      <td>${escapeHtml(row.code)}</td>
      <td>${row.codeLength}</td>
    `;
    els.codeTableBody.appendChild(tr);
  });
}

function renderAnalysis(data) {
  const analysis = data.analysis || {};
  const rows = [
    ["Original symbols", analysis.original_symbol_count],
    ["Unique symbols", analysis.unique_symbol_count],
    ["Original size", `${analysis.original_size_bytes} bytes / ${analysis.original_size_bits} bits`],
    ["Theoretical bitstream", `${analysis.theoretical_bitstream_bits} bits`],
    ["Stored .huff file", `${analysis.stored_file_bytes} bytes / ${analysis.stored_file_bits} bits`],
    ["Stored ratio", `${formatNumber(analysis.compression_ratio_stored)}:1`],
    ["Stored savings", `${formatNumber(analysis.space_savings_stored_pct)}%`],
    ["Entropy", `${formatNumber(analysis.entropy_bits_per_symbol, 4)} bits/symbol`],
    ["Average code length", `${formatNumber(analysis.average_code_length_bits, 4)} bits/symbol`],
  ];

  els.analysisList.replaceChildren();
  rows.forEach(([label, value]) => {
    const dt = document.createElement("dt");
    const dd = document.createElement("dd");
    dt.textContent = label;
    dd.textContent = value;
    els.analysisList.append(dt, dd);
  });
  els.entropyExplanation.textContent = data.entropyExplanation || "";
}

function renderComparison(comparison) {
  els.comparisonChart.replaceChildren();
  const rows = comparison?.rows || [];
  const implemented = rows.filter((row) => row.implemented && row.bits);
  const maxBits = Math.max(...implemented.map((row) => row.bits), 1);

  rows.forEach((row, index) => {
    const wrapper = document.createElement("div");
    wrapper.className = "bar-row";
    const bitsText = row.implemented && row.bits ? `${row.bits} bits` : "N/A";
    const width = row.implemented && row.bits ? Math.max(4, (row.bits / maxBits) * 100) : 0;
    wrapper.innerHTML = `
      <div class="bar-top">
        <strong>${escapeHtml(row.technique)}</strong>
        <span>${bitsText}</span>
      </div>
      <div class="bar-track"><i class="bar-fill ${index % 2 ? "secondary" : ""}" style="width:${width}%"></i></div>
    `;
    els.comparisonChart.appendChild(wrapper);
  });
}

function renderSizeChart(data) {
  const analysis = data.analysis || {};
  const rows = [
    {
      label: "Original",
      value: analysis.original_size_bits || 0,
      detail: `${analysis.original_size_bytes || 0} bytes`,
      tone: "",
    },
    {
      label: "Huffman Bitstream",
      value: analysis.theoretical_bitstream_bits || 0,
      detail: `${formatNumber(analysis.theoretical_bitstream_bytes || 0)} bytes`,
      tone: "accent",
    },
    {
      label: "Stored .huff",
      value: analysis.stored_file_bits || 0,
      detail: `${analysis.stored_file_bytes || 0} bytes`,
      tone: "warm",
    },
  ];
  const maxValue = Math.max(...rows.map((row) => row.value), 1);

  els.sizeChart.replaceChildren();
  rows.forEach((row) => {
    const width = Math.max(3, (row.value / maxValue) * 100);
    const item = document.createElement("div");
    item.className = "size-row";
    item.innerHTML = `
      <div class="size-top">
        <strong>${row.label}</strong>
        <span>${row.value} bits · ${row.detail}</span>
      </div>
      <div class="size-track"><i class="${row.tone}" style="width:${width}%"></i></div>
    `;
    els.sizeChart.appendChild(item);
  });
}

function renderTree(tree) {
  els.treeSvg.replaceChildren();
  if (!tree) {
    setTreeViewBox({ x: 0, y: 0, width: 900, height: 500 }, true);
    addSvgText(450, 250, "Run the pipeline to draw the Huffman tree.", "empty-text");
    return;
  }

  const leafGap = 86;
  const levelGap = 105;
  const marginX = 70;
  const marginY = 60;
  let leafIndex = 0;
  let maxDepth = 0;

  function assign(node, depth) {
    maxDepth = Math.max(maxDepth, depth);
    if (!node.children || node.children.length === 0) {
      node.x = marginX + leafIndex * leafGap;
      node.y = marginY + depth * levelGap;
      leafIndex += 1;
      return node.x;
    }

    const childXs = node.children.map((child) => assign(child, depth + 1));
    node.x = childXs.reduce((sum, value) => sum + value, 0) / childXs.length;
    node.y = marginY + depth * levelGap;
    return node.x;
  }

  assign(tree, 0);
  const width = Math.max(900, marginX * 2 + Math.max(leafIndex - 1, 1) * leafGap);
  const height = Math.max(560, marginY * 2 + maxDepth * levelGap + 80);
  setTreeViewBox({ x: 0, y: 0, width, height }, true);

  function drawEdges(node) {
    (node.children || []).forEach((child) => {
      const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
      line.setAttribute("x1", node.x);
      line.setAttribute("y1", node.y + 24);
      line.setAttribute("x2", child.x);
      line.setAttribute("y2", child.y - 24);
      line.setAttribute("class", "edge");
      els.treeSvg.appendChild(line);

      const midX = (node.x + child.x) / 2;
      const midY = (node.y + child.y) / 2;
      addSvgText(midX, midY, child.bit, "edge-label");
      drawEdges(child);
    });
  }

  function drawNodes(node) {
    const group = document.createElementNS("http://www.w3.org/2000/svg", "g");
    group.setAttribute("class", node.leaf ? "leaf-node" : "internal-node");
    group.style.animationDelay = `${Math.min((node.y / 105) * 70, 420)}ms`;

    const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    circle.setAttribute("cx", node.x);
    circle.setAttribute("cy", node.y);
    circle.setAttribute("r", 25);
    group.appendChild(circle);

    addSvgTextTo(group, node.x, node.y - 4, node.leaf ? node.symbol : String(node.frequency), "node-main");
    if (node.leaf) {
      addSvgTextTo(group, node.x, node.y + 13, String(node.frequency), "node-sub");
    }

    els.treeSvg.appendChild(group);
    (node.children || []).forEach(drawNodes);
  }

  drawEdges(tree);
  drawNodes(tree);
}

function addSvgText(x, y, text, className) {
  const node = document.createElementNS("http://www.w3.org/2000/svg", "text");
  node.setAttribute("x", x);
  node.setAttribute("y", y);
  node.setAttribute("class", className);
  node.textContent = text;
  els.treeSvg.appendChild(node);
  return node;
}

function addSvgTextTo(parent, x, y, text, className) {
  const node = document.createElementNS("http://www.w3.org/2000/svg", "text");
  node.setAttribute("x", x);
  node.setAttribute("y", y);
  node.setAttribute("class", className);
  node.textContent = text;
  parent.appendChild(node);
  return node;
}

async function decodeLastResult() {
  if (!state.compressedBase64) {
    showMessage("Run compression before decoding the last result.", "error");
    return;
  }
  await decodeBase64(state.compressedBase64, state.lastSourceText);
}

async function loadHuffFile(event) {
  const file = event.target.files[0];
  if (!file) {
    return;
  }
  const buffer = await file.arrayBuffer();
  const encoded = arrayBufferToBase64(buffer);
  await decodeBase64(encoded, els.sourceText.value);
  event.target.value = "";
}

async function decodeBase64(compressedBase64, originalText = "") {
  setBusy(true);
  setPipelineStage(5);
  showMessage("Decoding compressed data...");

  try {
    const response = await fetch("/api/decompress", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ compressedBase64, originalText }),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Decompression failed.");
    }

    els.decodedText.value = data.decodedText;
    els.downloadTextBtn.disabled = data.decodedText.length === 0;
    if (data.verification === true) {
      els.verifyMetric.textContent = "Passed";
      showMessage("Decoded successfully. Lossless verification passed.", "good");
    } else if (data.verification === false) {
      els.verifyMetric.textContent = "Failed";
      showMessage("Decoded, but it does not match the current source text.", "error");
    } else {
      els.verifyMetric.textContent = "Decoded";
      showMessage("Decoded successfully.");
    }
  } catch (error) {
    showMessage(error.message, "error");
  } finally {
    setBusy(false);
  }
}

async function loadTextFile(event) {
  const file = event.target.files[0];
  if (!file) {
    return;
  }
  try {
    els.sourceText.value = await file.text();
    updateInputMetric();
    showMessage(`Loaded ${file.name}.`);
  } catch {
    showMessage("Could not read that text file.", "error");
  } finally {
    event.target.value = "";
  }
}

async function loadSamples() {
  try {
    const response = await fetch("/api/samples");
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Could not load sample list.");
    }
    (data.samples || []).forEach((sample) => {
      const option = document.createElement("option");
      option.value = sample.id;
      option.textContent = sample.label;
      els.sampleSelect.appendChild(option);
    });
  } catch (error) {
    showMessage(error.message, "error");
  }
}

async function loadSelectedSample() {
  const sampleId = els.sampleSelect.value;
  if (!sampleId) {
    showMessage("Choose a demo sample first.", "error");
    return;
  }

  try {
    const response = await fetch(`/api/samples/${encodeURIComponent(sampleId)}`);
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Could not load sample.");
    }
    els.sourceText.value = data.text;
    state.result = null;
    state.codeRows = [];
    state.steps = [];
    state.compressedBase64 = "";
    state.lastSourceText = "";
    updateEmptyState();
    updateInputMetric();
    showMessage(`Loaded sample: ${data.label}.`);
  } catch (error) {
    showMessage(error.message, "error");
  }
}

function downloadCompressed() {
  if (!state.compressedBase64) {
    return;
  }
  const bytes = base64ToUint8Array(state.compressedBase64);
  downloadBlob(new Blob([bytes], { type: "application/octet-stream" }), "compressed_output.huff");
}

function exportReport() {
  if (!state.result) {
    showMessage("Run compression before exporting a report.", "error");
    return;
  }

  const data = state.result;
  const summary = data.summary;
  const rows = state.codeRows.slice(0, 80).map((row) => `
    <tr>
      <td>${escapeHtml(row.symbol)}</td>
      <td>${row.frequency}</td>
      <td>${formatNumber(row.probability, 4)}</td>
      <td>${escapeHtml(row.code)}</td>
      <td>${row.codeLength}</td>
    </tr>
  `).join("");
  const steps = state.steps.map((step, index) => `
    <li><strong>Step ${index + 1}.</strong> ${escapeHtml(step)}</li>
  `).join("");

  const report = `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Huffman Compression Report</title>
  <style>
    body { margin: 40px; color: #17202a; font-family: Segoe UI, Arial, sans-serif; line-height: 1.55; }
    h1 { margin-bottom: 6px; font-size: 34px; }
    h2 { margin-top: 28px; }
    .grid { display: grid; grid-template-columns: repeat(4, minmax(130px, 1fr)); gap: 12px; }
    .card { border: 1px solid #d8dee6; border-radius: 8px; padding: 14px; }
    .card span { color: #687385; font-size: 12px; font-weight: 700; text-transform: uppercase; }
    .card strong { display: block; margin-top: 6px; font-size: 20px; }
    table { width: 100%; border-collapse: collapse; margin-top: 12px; }
    th, td { border-bottom: 1px solid #e2e8f0; padding: 9px; text-align: left; font-family: Consolas, monospace; }
    th { background: #f3f6f9; }
    li { margin-bottom: 8px; }
    pre { white-space: pre-wrap; overflow-wrap: anywhere; background: #f6f8fb; padding: 14px; border-radius: 8px; }
  </style>
</head>
<body>
  <h1>Huffman Compression Report</h1>
  <p>Generated from Huffman Compression Studio.</p>
  <section class="grid">
    <article class="card"><span>Characters</span><strong>${summary.characters}</strong></article>
    <article class="card"><span>Unique Symbols</span><strong>${summary.uniqueSymbols}</strong></article>
    <article class="card"><span>Stored Size</span><strong>${summary.storedBytes} bytes</strong></article>
    <article class="card"><span>Stored Ratio</span><strong>${formatNumber(summary.compressionRatio)}:1</strong></article>
  </section>
  <h2>Compression Metrics</h2>
  <p>Original: ${data.analysis.original_size_bits} bits. Theoretical bitstream: ${data.analysis.theoretical_bitstream_bits} bits. Stored file: ${data.analysis.stored_file_bits} bits.</p>
  <p>Space savings: ${formatNumber(summary.spaceSavingsPct)}%. Entropy: ${formatNumber(summary.entropy, 4)} bits/symbol. Average code length: ${formatNumber(summary.averageCodeLength, 4)} bits/symbol.</p>
  <h2>Entropy Explanation</h2>
  <p>${escapeHtml(data.entropyExplanation)}</p>
  <h2>Bitstream Preview</h2>
  <pre>${escapeHtml(data.bitPreview || "")}</pre>
  <h2>Code Table</h2>
  <table>
    <thead><tr><th>Symbol</th><th>Frequency</th><th>Probability</th><th>Code</th><th>Length</th></tr></thead>
    <tbody>${rows}</tbody>
  </table>
  <h2>Algorithm Steps</h2>
  <ol>${steps}</ol>
</body>
</html>`;

  downloadBlob(new Blob([report], { type: "text/html;charset=utf-8" }), "huffman_report.html");
  showMessage("Report exported as huffman_report.html.", "good");
}

function downloadDecodedText() {
  downloadBlob(new Blob([els.decodedText.value], { type: "text/plain;charset=utf-8" }), "recovered_text.txt");
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

function moveStep(direction) {
  if (!state.steps.length) {
    return;
  }
  state.stepIndex = Math.max(0, Math.min(state.steps.length - 1, state.stepIndex + direction));
  renderStep();
}

function renderStep() {
  const total = state.steps.length;
  if (!total) {
    els.stepCounter.textContent = "Step 0 of 0";
    els.stepProgress.style.width = "0%";
    els.stepText.textContent = "Run the pipeline to review the exact heap and tree operations.";
    return;
  }
  els.stepCounter.textContent = `Step ${state.stepIndex + 1} of ${total}`;
  els.stepProgress.style.width = `${((state.stepIndex + 1) / total) * 100}%`;
  els.stepText.textContent = state.steps[state.stepIndex];
}

function setTreeViewBox(box, resetBase = false) {
  state.treeViewBox = { ...box };
  if (resetBase) {
    state.treeBaseViewBox = { ...box };
  }
  els.treeSvg.setAttribute(
    "viewBox",
    `${state.treeViewBox.x} ${state.treeViewBox.y} ${state.treeViewBox.width} ${state.treeViewBox.height}`
  );
}

function zoomTree(scale, clientX = null, clientY = null) {
  if (!state.treeViewBox) {
    return;
  }

  const rect = els.treeSvg.getBoundingClientRect();
  const anchorX = clientX === null ? 0.5 : (clientX - rect.left) / Math.max(1, rect.width);
  const anchorY = clientY === null ? 0.5 : (clientY - rect.top) / Math.max(1, rect.height);
  const nextWidth = Math.max(180, Math.min(state.treeBaseViewBox.width * 2.6, state.treeViewBox.width * scale));
  const nextHeight = Math.max(120, Math.min(state.treeBaseViewBox.height * 2.6, state.treeViewBox.height * scale));
  const dx = (state.treeViewBox.width - nextWidth) * anchorX;
  const dy = (state.treeViewBox.height - nextHeight) * anchorY;
  setTreeViewBox({
    x: state.treeViewBox.x + dx,
    y: state.treeViewBox.y + dy,
    width: nextWidth,
    height: nextHeight,
  });
}

function resetTreeView() {
  if (state.treeBaseViewBox) {
    setTreeViewBox(state.treeBaseViewBox);
  }
}

function onTreeWheel(event) {
  if (!state.treeViewBox) {
    return;
  }
  event.preventDefault();
  zoomTree(event.deltaY < 0 ? 0.88 : 1.14, event.clientX, event.clientY);
}

function startTreeDrag(event) {
  if (!state.treeViewBox) {
    return;
  }
  els.treeSvg.setPointerCapture(event.pointerId);
  state.treeDrag = {
    id: event.pointerId,
    x: event.clientX,
    y: event.clientY,
    box: { ...state.treeViewBox },
  };
}

function moveTreeDrag(event) {
  if (!state.treeDrag || state.treeDrag.id !== event.pointerId) {
    return;
  }
  const rect = els.treeSvg.getBoundingClientRect();
  const dx = ((event.clientX - state.treeDrag.x) / Math.max(1, rect.width)) * state.treeDrag.box.width;
  const dy = ((event.clientY - state.treeDrag.y) / Math.max(1, rect.height)) * state.treeDrag.box.height;
  setTreeViewBox({
    ...state.treeDrag.box,
    x: state.treeDrag.box.x - dx,
    y: state.treeDrag.box.y - dy,
  });
}

function endTreeDrag(event) {
  if (state.treeDrag?.id === event.pointerId) {
    state.treeDrag = null;
  }
}

function clearAll() {
  els.sourceText.value = "";
  els.decodedText.value = "";
  state.result = null;
  state.codeRows = [];
  state.steps = [];
  state.stepIndex = 0;
  state.compressedBase64 = "";
  state.lastSourceText = "";
  updateEmptyState();
  setPipelineStage(0);
  showMessage("Workspace cleared.");
}

function updateInputMetric() {
  const text = els.sourceText.value;
  const unique = new Set(text).size;
  els.sourceMetric.textContent = text ? `${text.length} chars${unique ? `, ${unique} unique` : ""}` : "No input";
  if (!state.result) {
    setPipelineStage(text.length ? 1 : 0);
  }
}

function updateEmptyState() {
  els.sourceMetric.textContent = "No input";
  els.codesMetric.textContent = "0 codes";
  els.storedMetric.textContent = "-";
  els.verifyMetric.textContent = "Not decoded";
  els.originalSize.textContent = "-";
  els.bitstreamSize.textContent = "-";
  els.ratioValue.textContent = "-";
  els.savingsValue.textContent = "-";
  els.bitPreview.textContent = "Run the pipeline to generate compressed bits.";
  els.frequencyList.textContent = "No symbols yet.";
  els.codeTableBody.innerHTML = `<tr><td colspan="5">Run the pipeline to populate the table.</td></tr>`;
  els.analysisList.replaceChildren();
  els.entropyExplanation.textContent = "";
  els.comparisonChart.textContent = "Run the pipeline to compare algorithms.";
  renderTree(null);
  renderStep();
  els.downloadCompressedBtn.disabled = true;
  els.exportReportBtn.disabled = true;
  els.downloadTextBtn.disabled = true;
  els.decodeLastBtn.disabled = true;
  setPipelineStage(0);
}

function setPipelineStage(stage) {
  state.pipelineStage = stage;
  const width = Math.max(0, Math.min(100, (stage / 5) * 100));
  els.pipelineProgress.style.width = `${width}%`;
  document.querySelectorAll(".pipeline-rail li").forEach((item, index) => {
    item.classList.toggle("active", index < stage);
  });
}

function setBusy(isBusy) {
  els.runBtn.disabled = isBusy;
  els.decodeLastBtn.disabled = isBusy || !state.compressedBase64;
}

function showMessage(text, mode = "") {
  els.message.textContent = text;
  els.message.className = `message ${mode}`;
}

function arrayBufferToBase64(buffer) {
  const bytes = new Uint8Array(buffer);
  let binary = "";
  bytes.forEach((byte) => {
    binary += String.fromCharCode(byte);
  });
  return btoa(binary);
}

function base64ToUint8Array(base64) {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index);
  }
  return bytes;
}

function formatNumber(value, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "-";
  }
  return Number(value).toFixed(digits);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function scrollToStudio() {
  els.studioApp.scrollIntoView({ behavior: "smooth", block: "start" });
  window.setTimeout(() => els.sourceText.focus({ preventScroll: true }), 650);
}

function resizeHeroCanvas() {
  const rect = els.heroCanvas.getBoundingClientRect();
  const ratio = window.devicePixelRatio || 1;
  els.heroCanvas.width = Math.max(1, Math.floor(rect.width * ratio));
  els.heroCanvas.height = Math.max(1, Math.floor(rect.height * ratio));
}

function drawHero() {
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const canvas = els.heroCanvas;
  const ctx = canvas.getContext("2d");
  const ratio = window.devicePixelRatio || 1;
  const width = canvas.width / ratio;
  const height = canvas.height / ratio;
  const tick = reduceMotion ? 32 : state.heroTick;
  const stage = state.pipelineStage / 5;

  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.save();
  ctx.scale(ratio, ratio);

  const horizontalLight = ctx.createLinearGradient(0, 0, width, height);
  horizontalLight.addColorStop(0, "#090d12");
  horizontalLight.addColorStop(0.48, "#111923");
  horizontalLight.addColorStop(1, "#090d12");
  ctx.fillStyle = horizontalLight;
  ctx.fillRect(0, 0, width, height);

  ctx.strokeStyle = "rgba(77, 208, 181, 0.09)";
  ctx.lineWidth = 1;
  for (let y = 48; y < height; y += 64) {
    ctx.beginPath();
    for (let x = 0; x <= width; x += 24) {
      const offset = Math.sin(x * 0.006 + tick * 0.018 + y * 0.02) * 12;
      if (x === 0) {
        ctx.moveTo(x, y + offset);
      } else {
        ctx.lineTo(x, y + offset);
      }
    }
    ctx.stroke();
  }

  const nodes = getHeroNodes(width, height, tick, stage);
  ctx.lineWidth = 1.4;
  nodes.forEach((node, index) => {
    for (let next = index + 1; next < nodes.length; next += 1) {
      const other = nodes[next];
      const distance = Math.hypot(node.x - other.x, node.y - other.y);
      if (distance < Math.min(width, 520) * 0.42) {
        const alpha = Math.max(0, 0.26 - distance / 1800);
        ctx.strokeStyle = `rgba(77, 208, 181, ${alpha})`;
        ctx.beginPath();
        ctx.moveTo(node.x, node.y);
        ctx.lineTo(other.x, other.y);
        ctx.stroke();
      }
    }
  });

  nodes.forEach((node, index) => {
    const pulse = Math.sin(tick * 0.035 + index) * 0.5 + 0.5;
    ctx.beginPath();
    ctx.fillStyle = index % 3 === 0
      ? `rgba(242, 184, 75, ${0.72 + pulse * 0.2})`
      : `rgba(77, 208, 181, ${0.68 + pulse * 0.25})`;
    ctx.arc(node.x, node.y, node.r + pulse * 2.4, 0, Math.PI * 2);
    ctx.fill();
  });

  drawBitStream(ctx, width, height, tick, stage);
  ctx.restore();

  if (!reduceMotion) {
    state.heroTick += 1;
  }
  requestAnimationFrame(drawHero);
}

function getHeroNodes(width, height, tick, stage) {
  const px = (state.pointer.x - 0.5) * 34;
  const py = (state.pointer.y - 0.5) * 24;
  const base = [
    [0.10, 0.28, 7], [0.18, 0.58, 5], [0.28, 0.42, 9],
    [0.42, 0.24, 6], [0.50, 0.56, 11], [0.62, 0.34, 8],
    [0.72, 0.62, 5], [0.83, 0.30, 10], [0.90, 0.54, 6],
  ];
  return base.map(([x, y, r], index) => ({
    x: width * x + Math.sin(tick * 0.014 + index) * (10 + stage * 14) + px,
    y: height * y + Math.cos(tick * 0.017 + index) * (10 + stage * 10) + py,
    r,
  }));
}

function drawBitStream(ctx, width, height, tick, stage) {
  const text = state.result?.bitPreview || "01001000 01110101 01100110 01100110 01101101 01100001 01101110";
  ctx.font = "800 12px Consolas, Courier New, monospace";
  const rows = 5;
  for (let row = 0; row < rows; row += 1) {
    const y = height * (0.22 + row * 0.13);
    for (let i = 0; i < width / 28; i += 1) {
      const index = (i + row * 7 + Math.floor(tick / 10)) % text.length;
      const char = text[index] === " " ? "" : text[index];
      const x = ((i * 28 - tick * (0.28 + row * 0.06)) % (width + 80)) - 40;
      const alpha = 0.12 + stage * 0.14 + (row / rows) * 0.06;
      ctx.fillStyle = `rgba(244, 247, 251, ${alpha})`;
      ctx.fillText(/[01]/.test(char) ? char : "", x, y);
    }
  }
}

function resizeSignalCanvas() {
  const rect = els.signalCanvas.getBoundingClientRect();
  const ratio = window.devicePixelRatio || 1;
  els.signalCanvas.width = Math.max(1, Math.floor(rect.width * ratio));
  els.signalCanvas.height = Math.max(1, Math.floor(rect.height * ratio));
}

function drawSignal() {
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const canvas = els.signalCanvas;
  const ctx = canvas.getContext("2d");
  const width = canvas.width;
  const height = canvas.height;
  const ratio = window.devicePixelRatio || 1;
  const source = state.result?.bitPreview || els.sourceText.value || "010011010111001010";
  const stageBoost = state.pipelineStage / 5;

  ctx.clearRect(0, 0, width, height);
  ctx.save();
  ctx.scale(ratio, ratio);

  const cssWidth = width / ratio;
  const cssHeight = height / ratio;
  const tick = reduceMotion ? 24 : state.signalTick;

  ctx.fillStyle = "#0d1218";
  ctx.fillRect(0, 0, cssWidth, cssHeight);

  ctx.strokeStyle = "rgba(77, 208, 181, 0.14)";
  ctx.lineWidth = 1;
  for (let x = -40 + (tick % 40); x < cssWidth + 40; x += 40) {
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x + 34, cssHeight);
    ctx.stroke();
  }

  ctx.font = "700 13px Consolas, Courier New, monospace";
  const columns = Math.max(12, Math.floor(cssWidth / 22));
  for (let i = 0; i < columns; i += 1) {
    const char = source[(i + Math.floor(tick / 8)) % source.length];
    const x = i * 22 + 10;
    const wave = Math.sin((i * 0.7) + (tick * 0.055));
    const y = cssHeight / 2 + wave * (22 + stageBoost * 14);
    const alpha = 0.32 + ((wave + 1) / 2) * 0.5;
    ctx.fillStyle = `rgba(77, 208, 181, ${alpha})`;
    ctx.fillText(/[01]/.test(char) ? char : char.charCodeAt(0).toString(2).slice(-1), x, y);
  }

  ctx.strokeStyle = "rgba(242, 184, 75, 0.75)";
  ctx.lineWidth = 2;
  ctx.beginPath();
  for (let x = 0; x <= cssWidth; x += 8) {
    const y = cssHeight * 0.72 + Math.sin((x * 0.025) + (tick * 0.05)) * (8 + stageBoost * 8);
    if (x === 0) {
      ctx.moveTo(x, y);
    } else {
      ctx.lineTo(x, y);
    }
  }
  ctx.stroke();

  ctx.restore();
  if (!reduceMotion) {
    state.signalTick += 1;
  }
  requestAnimationFrame(drawSignal);
}
