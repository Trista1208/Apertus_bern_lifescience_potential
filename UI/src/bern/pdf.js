// Renders the proposal letter to a real A4 PDF in the browser (html2canvas + jsPDF from cdnjs,
// loaded on first use so the app has no extra npm dependency).
// Inside a claude.ai artifact the file goes through the `downloads` capability; elsewhere jsPDF saves it.

const LIBS = [
  "https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js",
  "https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js",
];

function loadScript(src) {
  if (document.querySelector(`script[src="${src}"]`)) return Promise.resolve();
  return new Promise((resolve, reject) => {
    const s = document.createElement("script");
    s.src = src;
    s.onload = resolve;
    s.onerror = () => reject(new Error("Could not load the PDF library. Check your internet connection."));
    document.head.appendChild(s);
  });
}

export async function letterToPdf(el) {
  for (const src of LIBS) await loadScript(src);
  await document.fonts?.ready;
  const canvas = await window.html2canvas(el, {
    scale: 2,
    backgroundColor: "#ffffff",
    windowWidth: 1100,
    onclone: (doc) => {
      const c = doc.getElementById(el.id);
      if (c) { c.style.width = "794px"; c.style.maxWidth = "794px"; c.style.boxShadow = "none"; c.style.padding = "56px 64px"; }
    },
  });
  const { jsPDF } = window.jspdf;
  const pdf = new jsPDF({ unit: "pt", format: "a4" });
  const pw = pdf.internal.pageSize.getWidth();
  const ph = pdf.internal.pageSize.getHeight();
  const imgH = (canvas.height * pw) / canvas.width;
  const img = canvas.toDataURL("image/jpeg", 0.92);
  for (let y = 0, page = 0; y < imgH - 1; y += ph, page++) {
    if (page) pdf.addPage();
    pdf.addImage(img, "JPEG", 0, -y, pw, imgH);
  }
  return pdf;
}

// Returns "saved", "declined" or throws with a readable message.
export async function downloadLetter(el, filename) {
  const pdf = await letterToPdf(el);
  const downloads = window.claude?.use ? await window.claude.use("downloads") : null;
  if (downloads) {
    try {
      await downloads.save({ filename, data: pdf.output("blob") });
      return "saved";
    } catch (e) {
      if (e?.code === "declined") return "declined";
      throw new Error(e?.message || "The download was not allowed in this view.");
    }
  }
  if (window.claude) throw new Error("Downloads aren't available in this view.");
  pdf.save(filename);
  return "saved";
}
