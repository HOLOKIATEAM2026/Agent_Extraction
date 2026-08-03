const fileInput = document.getElementById('fileInput');
const modelSelect = document.getElementById('modelSelect');
const approachSelect = document.getElementById('approachSelect');
const btnExtract = document.getElementById('btnExtract');
const statusText = document.getElementById('statusText');
const resultsSection = document.getElementById('results');
const cardsGrid = document.getElementById('cardsGrid');
const jsonOutput = document.getElementById('jsonOutput');
const btnCopy = document.getElementById('btnCopy');
const btnExportPdf = document.getElementById('btnExportPdf');

function tr(key, vars) {
  if (window.I18n && typeof window.I18n.t === 'function') {
    return window.I18n.t(key, vars);
  }
  return key;
}

const EXPORT_SECTIONS = [
  { key: 'diagnostic_strategique', title: 'Diagnostic Strategique' },
  { key: 'diagnostic_financier', title: 'Diagnostic Financier' },
  { key: 'diagnostic_rh', title: 'Diagnostic RH' },
  { key: 'diagnostic_data', title: 'Maturite Data' },
  { key: 'diagnostic_cyber_gouvernance', title: 'Cyber & Gouvernance' }
];

function hasFieldValue(fieldData) {
  if (!fieldData) return false;
  if (Array.isArray(fieldData.valeur)) return fieldData.valeur.length > 0;
  return fieldData.valeur !== null && fieldData.valeur !== undefined && String(fieldData.valeur).trim() !== '';
}

function fieldToText(fieldData) {
  if (!fieldData || !hasFieldValue(fieldData)) return 'Non specifie';
  if (Array.isArray(fieldData.valeur)) return fieldData.valeur.join(', ');
  return String(fieldData.valeur);
}

function cleanPdfText(text) {
  return String(text || '')
    .replace(/[^\x20-\x7E\u00A0-\u017F]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function labelFromKey(key) {
  return String(key || '').replace(/_/g, ' ').replace(/\b\w/g, (m) => m.toUpperCase());
}

function getExportFileName(data) {
  const company = (((data || {}).meta || {}).entreprise || 'diagnostic').toString();
  const safe = company.replace(/[<>:"/\\|?*\x00-\x1F]/g, '_').replace(/\s+/g, '_');
  return `Holokia_Diagnostic_${safe}.pdf`;
}

async function loadLogoDataUrl() {
  const candidates = [
    'logo/cropped-logo_holokia_noir.avif',
    'logo/cropped-logo_holokia_noir.jpg'
  ];
  for (const src of candidates) {
    try {
      const img = await new Promise((resolve, reject) => {
        const el = new Image();
        el.crossOrigin = 'anonymous';
        el.onload = () => resolve(el);
        el.onerror = reject;
        el.src = src;
      });
      const canvas = document.createElement('canvas');
      canvas.width = img.naturalWidth || img.width;
      canvas.height = img.naturalHeight || img.height;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(img, 0, 0);
      return canvas.toDataURL('image/png');
    } catch (_) {}
  }
  return null;
}

function fillTemplate(template, vars) {
  let out = String(template || '');
  Object.entries(vars || {}).forEach(([key, value]) => {
    out = out.replace(new RegExp(`\\{${key}\\}`, 'g'), String(value ?? ''));
  });
  return out;
}

function tPdf(key, fallback, vars) {
  const translated = tr(key, vars);
  if (translated && translated !== key) return translated;
  return fillTemplate(fallback, vars || {});
}

function getSourceFileName(meta) {
  const source = meta && meta.source_file ? String(meta.source_file) : '';
  if (!source) return '';
  const parts = source.split(/[\\/]+/);
  return parts[parts.length - 1] || '';
}

function shortenText(text, max = 120) {
  const safe = cleanPdfText(text);
  if (safe.length <= max) return safe;
  return `${safe.slice(0, Math.max(0, max - 3)).trim()}...`;
}

function getFieldConfidence(fieldData) {
  const raw = Number(fieldData && fieldData.confiance);
  if (!Number.isFinite(raw)) return 0;
  return Math.max(0, Math.min(1, raw));
}

function getSectionMetrics(data) {
  const stats = [];
  let totalExpected = 0;
  let totalFilled = 0;
  let totalConfidence = 0;
  let totalConfidenceCount = 0;
  let totalFoundFields = 0;
  const missingLabels = [];

  EXPORT_SECTIONS.forEach((section) => {
    const sectionData = data && data[section.key] ? data[section.key] : {};
    const fieldKeys = Object.keys(sectionData);
    let filled = 0;
    let found = 0;
    let confidenceSum = 0;
    let confidenceCount = 0;
    const weakFields = [];

    fieldKeys.forEach((fieldKey) => {
      const fieldData = sectionData[fieldKey];
      const confidence = getFieldConfidence(fieldData);
      const hasValue = hasFieldValue(fieldData);
      if (hasValue) found += 1;
      if (hasValue && confidence >= 0.6) {
        filled += 1;
      } else {
        weakFields.push(labelFromKey(fieldKey));
        missingLabels.push(labelFromKey(fieldKey));
      }
      confidenceSum += confidence;
      confidenceCount += 1;
      totalConfidence += confidence;
      totalConfidenceCount += 1;
    });

    totalExpected += fieldKeys.length;
    totalFilled += filled;
    totalFoundFields += found;
    stats.push({
      key: section.key,
      title: section.title,
      fieldCount: fieldKeys.length,
      foundCount: found,
      filledCount: filled,
      avgConfidence: confidenceCount ? (confidenceSum / confidenceCount) * 100 : 0,
      weakFields: weakFields.slice(0, 4),
      data: sectionData
    });
  });

  const avgConfidence = totalConfidenceCount ? (totalConfidence / totalConfidenceCount) * 100 : 0;
  const completeness = totalExpected ? (totalFilled / totalExpected) * 100 : 0;
  const quality = (avgConfidence * completeness) / 100;

  return {
    sectionStats: stats,
    totalExpected,
    totalFilled,
    totalFoundFields,
    avgConfidence,
    completeness,
    quality,
    missingLabels: Array.from(new Set(missingLabels))
  };
}

function getRecommendationPriority(rec, index) {
  const raw = String((rec && (rec.priorite || rec.priority || rec.niveau)) || '').toLowerCase();
  if (raw.includes('haut') || raw.includes('high') || raw.includes('critical')) {
    return { label: 'Haute', fill: [254, 226, 226], text: [185, 28, 28], impact: 5 };
  }
  if (raw.includes('faib') || raw.includes('low')) {
    return { label: 'Faible', fill: [220, 252, 231], text: [22, 101, 52], impact: 2 };
  }
  if (raw.includes('moy') || raw.includes('medium')) {
    return { label: 'Moyenne', fill: [255, 237, 213], text: [194, 65, 12], impact: 3 };
  }
  if (index === 0) return { label: 'Haute', fill: [254, 226, 226], text: [185, 28, 28], impact: 5 };
  if (index === 1) return { label: 'Moyenne', fill: [255, 237, 213], text: [194, 65, 12], impact: 4 };
  return { label: 'Faible', fill: [220, 252, 231], text: [22, 101, 52], impact: 3 };
}

async function exportDiagnosticPdf(data) {
  if (!data) {
    alert(tr('diagnostic.export_no_data'));
    return;
  }
  if (!window.jspdf || !window.jspdf.jsPDF) {
    alert(tr('diagnostic.export_lib_missing'));
    return;
  }

  const { jsPDF } = window.jspdf;
  const pdf = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
  const pageWidth = pdf.internal.pageSize.getWidth();
  const pageHeight = pdf.internal.pageSize.getHeight();
  const margin = 15;
  const contentWidth = pageWidth - (margin * 2);
  const footerHeight = 14;
  const topContentY = 28;
  const tableFontSize = 8.5;
  const colors = {
    brand: [15, 98, 254],
    navy: [22, 53, 93],
    light: [245, 247, 250],
    surface: [255, 255, 255],
    border: [216, 223, 232],
    text: [22, 28, 45],
    muted: [97, 108, 124],
    success: [22, 163, 74],
    warning: [245, 158, 11],
    danger: [220, 38, 38],
    paleBlue: [239, 244, 255]
  };
  let y = topContentY;

  const meta = (data && data.meta) || {};
  const sourceFileName = getSourceFileName(meta) || `${meta.entreprise || 'document'}.pdf`;
  const metrics = getSectionMetrics(data);
  const recommendations = Array.isArray(data.recommandations) ? data.recommandations.slice(0, 3) : [];
  const questionsUsed = Array.isArray(meta.questions_utilisees) ? meta.questions_utilisees : [];
  const generatedAt = new Date();
  const sectionOverviewRows = metrics.sectionStats
    .filter((section) => section.fieldCount > 0)
    .map((section) => [
      section.title,
      `${section.filledCount}/${section.fieldCount}`,
      `${Math.round(section.avgConfidence)}%`,
      section.weakFields.length ? section.weakFields.join(', ') : tPdf('diagnostic.pdf_status_ok', 'RAS')
    ]);

  const executiveSummary = (() => {
    const weakest = metrics.sectionStats
      .filter((section) => section.fieldCount > 0)
      .sort((a, b) => a.avgConfidence - b.avgConfidence)
      .slice(0, 2)
      .map((section) => section.title);
    const weakPart = weakest.length
      ? tPdf('diagnostic.pdf_exec_weak_part', 'Les points a renforcer concernent principalement {areas}.', { areas: weakest.join(', ') })
      : tPdf('diagnostic.pdf_exec_weak_none', 'Aucune zone critique n a ete detectee dans les sections analysees.');
    const missingPart = metrics.missingLabels.length
      ? tPdf(
          'diagnostic.pdf_exec_missing_part',
          'Les champs a consolider en priorite sont {fields}.',
          { fields: metrics.missingLabels.slice(0, 4).join(', ') }
        )
      : tPdf('diagnostic.pdf_exec_missing_none', 'Les informations attendues sont globalement presentes et sourcables.');
    return [
      tPdf(
        'diagnostic.pdf_exec_intro',
        'Le diagnostic automatique de {company} indique une completude de {completeness}% et une confiance moyenne de {confidence}%.',
        {
          company: meta.entreprise || tPdf('diagnostic.pdf_not_specified', 'Non specifie'),
          completeness: Math.round(metrics.completeness),
          confidence: Math.round(metrics.avgConfidence)
        }
      ),
      weakPart,
      missingPart,
      recommendations.length
        ? tPdf(
            'diagnostic.pdf_exec_reco',
            '{count} action(s) prioritaire(s) sont recommandees pour ameliorer la qualite documentaire et la fiabilite des sources.',
            { count: recommendations.length }
          )
        : tPdf('diagnostic.pdf_exec_reco_none', 'Aucune recommandation automatique supplementaire n a ete generee.')
    ].join(' ');
  })();

  pdf.setProperties({
    title: cleanPdfText(tPdf('diagnostic.pdf_meta_title', 'Rapport de Diagnostic IA')),
    author: 'Holokia',
    subject: cleanPdfText(tPdf('diagnostic.pdf_meta_subject', 'Analyse documentaire automatisee')),
    creator: 'Holokia',
    keywords: cleanPdfText(`Holokia, diagnostic, RAG, ${meta.entreprise || ''}`),
    producer: 'Holokia'
  });

  const ensureSpace = (needed = 10, nextPageTop = topContentY) => {
    if (y + needed > pageHeight - footerHeight - 6) {
      pdf.addPage();
      y = nextPageTop;
    }
  };

  const drawWrapped = (text, x, size = 10, color = colors.text, gapAfter = 2, width = contentWidth - (x - margin), fontStyle = 'normal', lineGap = 4.8) => {
    const safe = cleanPdfText(text);
    if (!safe) return;
    pdf.setFont('helvetica', fontStyle);
    pdf.setFontSize(size);
    pdf.setTextColor(color[0], color[1], color[2]);
    const lines = pdf.splitTextToSize(safe, width);
    lines.forEach((line) => {
      ensureSpace(lineGap + 1);
      pdf.text(line, x, y);
      y += lineGap;
    });
    y += gapAfter;
  };

  const drawBadge = (x, badgeY, label, fillColor, textColor, w = 24) => {
    pdf.setFillColor(fillColor[0], fillColor[1], fillColor[2]);
    pdf.setDrawColor(fillColor[0], fillColor[1], fillColor[2]);
    pdf.roundedRect(x, badgeY, w, 7, 2, 2, 'FD');
    pdf.setFont('helvetica', 'bold');
    pdf.setFontSize(8);
    pdf.setTextColor(textColor[0], textColor[1], textColor[2]);
    pdf.text(cleanPdfText(label), x + (w / 2), badgeY + 4.5, { align: 'center' });
  };

  const drawSectionTitle = (kicker, title, subtitle) => {
    ensureSpace(18);
    pdf.setDrawColor(colors.brand[0], colors.brand[1], colors.brand[2]);
    pdf.setLineWidth(0.7);
    pdf.line(margin, y, pageWidth - margin, y);
    y += 5;
    if (kicker) {
      pdf.setFont('helvetica', 'bold');
      pdf.setFontSize(8.5);
      pdf.setTextColor(colors.brand[0], colors.brand[1], colors.brand[2]);
      pdf.text(cleanPdfText(kicker), margin, y);
      y += 5;
    }
    pdf.setFont('helvetica', 'bold');
    pdf.setFontSize(17);
    pdf.setTextColor(colors.navy[0], colors.navy[1], colors.navy[2]);
    pdf.text(cleanPdfText(title), margin, y);
    y += 6;
    if (subtitle) {
      drawWrapped(subtitle, margin, 9.5, colors.muted, 3, contentWidth, 'normal', 4.2);
    }
  };

  const drawKpiCard = (x, cardY, w, h, label, value, caption, accent) => {
    pdf.setFillColor(colors.surface[0], colors.surface[1], colors.surface[2]);
    pdf.setDrawColor(colors.border[0], colors.border[1], colors.border[2]);
    pdf.roundedRect(x, cardY, w, h, 4, 4, 'FD');
    pdf.setFillColor(accent[0], accent[1], accent[2]);
    pdf.roundedRect(x + 3, cardY + 3, 2.5, h - 6, 1, 1, 'F');
    pdf.setFont('helvetica', 'bold');
    pdf.setFontSize(9);
    pdf.setTextColor(colors.muted[0], colors.muted[1], colors.muted[2]);
    pdf.text(cleanPdfText(label), x + 9, cardY + 8);
    pdf.setFont('helvetica', 'bold');
    pdf.setFontSize(20);
    pdf.setTextColor(colors.navy[0], colors.navy[1], colors.navy[2]);
    pdf.text(cleanPdfText(value), x + 9, cardY + 18);
    pdf.setFont('helvetica', 'normal');
    pdf.setFontSize(8.5);
    pdf.setTextColor(colors.muted[0], colors.muted[1], colors.muted[2]);
    const lines = pdf.splitTextToSize(cleanPdfText(caption), w - 14);
    lines.slice(0, 2).forEach((line, index) => {
      pdf.text(line, x + 9, cardY + 25 + (index * 4));
    });
  };

  const drawTable = (columns, rows, widths, options = {}) => {
    const startX = options.x || margin;
    const headerFill = options.headerFill || colors.navy;
    const headerText = options.headerText || [255, 255, 255];
    const bodyFontSize = options.bodyFontSize || tableFontSize;
    const lineSize = options.lineSize || 3.8;
    const rowPadding = options.rowPadding || 2.2;
    const headerHeight = options.headerHeight || 8;

    const drawHeader = () => {
      ensureSpace(headerHeight + 1);
      let x = startX;
      pdf.setFillColor(headerFill[0], headerFill[1], headerFill[2]);
      pdf.setDrawColor(colors.border[0], colors.border[1], colors.border[2]);
      columns.forEach((column, idx) => {
        pdf.rect(x, y, widths[idx], headerHeight, 'FD');
        pdf.setFont('helvetica', 'bold');
        pdf.setFontSize(8.5);
        pdf.setTextColor(headerText[0], headerText[1], headerText[2]);
        pdf.text(cleanPdfText(column), x + 2, y + 5.2);
        x += widths[idx];
      });
      y += headerHeight;
    };

    drawHeader();
    rows.forEach((row, rowIndex) => {
      const cellLines = row.map((cell, idx) => {
        pdf.setFont('helvetica', 'normal');
        pdf.setFontSize(bodyFontSize);
        return pdf.splitTextToSize(cleanPdfText(cell), widths[idx] - 4);
      });
      const rowHeight = Math.max(...cellLines.map((lines) => Math.max(lines.length, 1))) * lineSize + (rowPadding * 2);
      if (y + rowHeight > pageHeight - footerHeight - 6) {
        pdf.addPage();
        y = topContentY;
        drawHeader();
      }

      let x = startX;
      const fill = rowIndex % 2 === 0 ? [255, 255, 255] : colors.light;
      row.forEach((_, idx) => {
        pdf.setFillColor(fill[0], fill[1], fill[2]);
        pdf.setDrawColor(colors.border[0], colors.border[1], colors.border[2]);
        pdf.rect(x, y, widths[idx], rowHeight, 'FD');
        pdf.setFont('helvetica', 'normal');
        pdf.setFontSize(bodyFontSize);
        pdf.setTextColor(colors.text[0], colors.text[1], colors.text[2]);
        cellLines[idx].forEach((line, lineIndex) => {
          pdf.text(line, x + 2, y + rowPadding + 2.6 + (lineIndex * lineSize));
        });
        x += widths[idx];
      });
      y += rowHeight;
    });
    y += 4;
  };

  const drawRecommendationCard = (rec, index) => {
    const priority = getRecommendationPriority(rec, index);
    const cardHeight = 38;
    ensureSpace(cardHeight + 4);
    pdf.setFillColor(255, 255, 255);
    pdf.setDrawColor(colors.border[0], colors.border[1], colors.border[2]);
    pdf.roundedRect(margin, y, contentWidth, cardHeight, 4, 4, 'FD');
    drawBadge(pageWidth - margin - 28, y + 4, priority.label, priority.fill, priority.text, 28);
    pdf.setFont('helvetica', 'bold');
    pdf.setFontSize(11.5);
    pdf.setTextColor(colors.navy[0], colors.navy[1], colors.navy[2]);
    pdf.text(cleanPdfText(rec.titre || tPdf('diagnostic.pdf_action', 'Action prioritaire')), margin + 4, y + 9);
    let localY = y + 15;
    const actionLines = pdf.splitTextToSize(cleanPdfText(rec.action || ''), contentWidth - 10);
    pdf.setFont('helvetica', 'normal');
    pdf.setFontSize(9.5);
    pdf.setTextColor(colors.text[0], colors.text[1], colors.text[2]);
    actionLines.slice(0, 3).forEach((line) => {
      pdf.text(line, margin + 4, localY);
      localY += 4.3;
    });
    const justification = rec.raison
      ? tPdf('diagnostic.pdf_justification', 'Justification: {reason}', { reason: rec.raison })
      : '';
    if (justification) {
      const justLines = pdf.splitTextToSize(cleanPdfText(justification), contentWidth - 10);
      pdf.setFontSize(8.5);
      pdf.setTextColor(colors.muted[0], colors.muted[1], colors.muted[2]);
      justLines.slice(0, 2).forEach((line) => {
        pdf.text(line, margin + 4, localY);
        localY += 4;
      });
    }
    pdf.setFont('helvetica', 'bold');
    pdf.setFontSize(8.5);
    pdf.setTextColor(colors.brand[0], colors.brand[1], colors.brand[2]);
    pdf.text(
      cleanPdfText(
        tPdf('diagnostic.pdf_expected_impact', 'Impact attendu: {stars}', {
          stars: '★'.repeat(priority.impact)
        })
      ),
      margin + 4,
      y + cardHeight - 4
    );
    y += cardHeight + 4;
  };

  const finalizeDocument = () => {
    const totalPages = pdf.getNumberOfPages();
    for (let page = 1; page <= totalPages; page += 1) {
      pdf.setPage(page);
      if (page > 1) {
        pdf.setTextColor(236, 240, 247);
        pdf.setFont('helvetica', 'bold');
        pdf.setFontSize(34);
        pdf.text(
          cleanPdfText(tPdf('diagnostic.pdf_confidential', 'CONFIDENTIEL')),
          pageWidth / 2,
          pageHeight / 2,
          { align: 'center', angle: 35 }
        );
      }
      pdf.setDrawColor(colors.border[0], colors.border[1], colors.border[2]);
      pdf.line(margin, pageHeight - footerHeight, pageWidth - margin, pageHeight - footerHeight);
      pdf.setFont('helvetica', 'normal');
      pdf.setFontSize(8);
      pdf.setTextColor(colors.muted[0], colors.muted[1], colors.muted[2]);
      pdf.text(cleanPdfText(tPdf('diagnostic.pdf_footer', '© Holokia 2026 · Rapport genere automatiquement')), margin, pageHeight - 8);
      pdf.text(
        cleanPdfText(
          tPdf('diagnostic.pdf_page', 'Page {page} / {total}', { page, total: totalPages })
        ),
        pageWidth - margin,
        pageHeight - 8,
        { align: 'right' }
      );
    }
  };

  const logoDataUrl = await loadLogoDataUrl();

  pdf.setFillColor(colors.light[0], colors.light[1], colors.light[2]);
  pdf.rect(0, 0, pageWidth, pageHeight, 'F');
  pdf.setFillColor(colors.navy[0], colors.navy[1], colors.navy[2]);
  pdf.rect(0, 0, pageWidth, 62, 'F');
  pdf.setFillColor(colors.brand[0], colors.brand[1], colors.brand[2]);
  pdf.rect(0, 62, pageWidth, 4, 'F');

  if (logoDataUrl) {
    try {
      pdf.addImage(logoDataUrl, 'PNG', margin, 15, 42, 22);
    } catch (_) {}
  }

  pdf.setFont('helvetica', 'bold');
  pdf.setFontSize(25);
  pdf.setTextColor(255, 255, 255);
  pdf.text(cleanPdfText(tPdf('diagnostic.pdf_report_title', 'RAPPORT DE DIAGNOSTIC IA')), margin, 82);
  pdf.setFont('helvetica', 'normal');
  pdf.setFontSize(11);
  pdf.text(cleanPdfText(tPdf('diagnostic.pdf_report_subtitle', 'Analyse automatique des documents et synthese executive')), margin, 90);

  pdf.setFillColor(255, 255, 255);
  pdf.setDrawColor(colors.border[0], colors.border[1], colors.border[2]);
  pdf.roundedRect(margin, 108, contentWidth, 84, 5, 5, 'FD');

  pdf.setFont('helvetica', 'bold');
  pdf.setFontSize(12);
  pdf.setTextColor(colors.navy[0], colors.navy[1], colors.navy[2]);
  pdf.text(cleanPdfText(tPdf('diagnostic.pdf_general_info', 'Informations generales')), margin + 6, 119);

  const coverLines = [
    `${tPdf('diagnostic.pdf_company_label', 'Entreprise')} : ${cleanPdfText(meta.entreprise || tPdf('diagnostic.pdf_not_specified', 'Non specifie'))}`,
    `${tPdf('diagnostic.pdf_document_label', 'Document')} : ${cleanPdfText(sourceFileName)}`,
    `${tPdf('diagnostic.pdf_export_date_label', 'Date')} : ${cleanPdfText(generatedAt.toLocaleDateString())}`,
    `${tPdf('diagnostic.pdf_export_time_label', 'Heure')} : ${cleanPdfText(generatedAt.toLocaleTimeString())}`,
    `${tPdf('diagnostic.pdf_model_label', 'Modele')} : ${cleanPdfText(meta.modele_utilise || tPdf('diagnostic.pdf_not_specified', 'Non specifie'))}`,
    `${tPdf('diagnostic.pdf_provider_label', 'Provider')} : ${cleanPdfText(meta.provider || tPdf('diagnostic.pdf_not_specified', 'Non specifie'))}`,
    `${tPdf('diagnostic.pdf_version_label', 'Version')} : v1.1`
  ];
  let coverY = 130;
  coverLines.forEach((line) => {
    pdf.setFont('helvetica', 'normal');
    pdf.setFontSize(10.5);
    pdf.setTextColor(colors.text[0], colors.text[1], colors.text[2]);
    pdf.text(line, margin + 6, coverY);
    coverY += 9;
  });

  drawBadge(margin, 203, tPdf('diagnostic.pdf_confidential', 'CONFIDENTIEL'), [226, 232, 240], colors.navy, 42);
  pdf.setFont('helvetica', 'normal');
  pdf.setFontSize(9.5);
  pdf.setTextColor(colors.muted[0], colors.muted[1], colors.muted[2]);
  const coverNoteLines = pdf.splitTextToSize(
    cleanPdfText(tPdf('diagnostic.pdf_cover_note', 'Document genere automatiquement pour usage interne et client.')),
    contentWidth - 48
  );
  coverNoteLines.slice(0, 2).forEach((line, index) => {
    pdf.text(line, margin + 48, 207 + (index * 4));
  });

  pdf.addPage();
  y = topContentY;

  drawSectionTitle(
    tPdf('diagnostic.pdf_summary_kicker', 'RESUME EXECUTIF'),
    tPdf('diagnostic.pdf_summary_title', 'Synthese de pilotage'),
    tPdf('diagnostic.pdf_summary_subtitle', 'Lecture rapide pour la direction et les equipes projet')
  );
  drawWrapped(executiveSummary, margin, 10.5, colors.text, 5, contentWidth, 'normal', 4.9);

  const cardGap = 6;
  const cardWidth = (contentWidth - cardGap) / 2;
  const cardHeight = 31;
  const cardY = y;
  drawKpiCard(
    margin,
    cardY,
    cardWidth,
    cardHeight,
    tPdf('diagnostic.pdf_kpi_completeness', 'Completude'),
    `${Math.round(metrics.completeness)}%`,
    tPdf('diagnostic.pdf_kpi_completeness_caption', 'Champs fiables / champs attendus'),
    colors.brand
  );
  drawKpiCard(
    margin + cardWidth + cardGap,
    cardY,
    cardWidth,
    cardHeight,
    tPdf('diagnostic.pdf_kpi_confidence', 'Confiance'),
    `${Math.round(metrics.avgConfidence)}%`,
    tPdf('diagnostic.pdf_kpi_confidence_caption', 'Moyenne des confiances extraites'),
    colors.success
  );
  drawKpiCard(
    margin,
    cardY + cardHeight + 6,
    cardWidth,
    cardHeight,
    tPdf('diagnostic.pdf_kpi_documents', 'Documents'),
    '1',
    tPdf('diagnostic.pdf_kpi_documents_caption', 'Rapport analyse dans cette extraction'),
    colors.warning
  );
  drawKpiCard(
    margin + cardWidth + cardGap,
    cardY + cardHeight + 6,
    cardWidth,
    cardHeight,
    tPdf('diagnostic.pdf_kpi_quality', 'Score global'),
    `${Math.round(metrics.quality)}%`,
    tPdf('diagnostic.pdf_kpi_quality_caption', 'Confiance x completude'),
    colors.navy
  );
  y = cardY + (cardHeight * 2) + 12;

  drawSectionTitle(
    tPdf('diagnostic.pdf_overview_kicker', 'PILOTAGE'),
    tPdf('diagnostic.pdf_section_overview', 'Vue d ensemble des sections'),
    tPdf('diagnostic.pdf_section_overview_subtitle', 'Couverture et niveau de confiance par domaine')
  );
  drawTable(
    [
      tPdf('diagnostic.pdf_table_section', 'Section'),
      tPdf('diagnostic.pdf_table_coverage', 'Couverture'),
      tPdf('diagnostic.pdf_table_confidence', 'Confiance'),
      tPdf('diagnostic.pdf_table_watchouts', 'Points de vigilance')
    ],
    sectionOverviewRows,
    [42, 28, 26, 86]
  );

  drawSectionTitle(
    tPdf('diagnostic.pdf_documents_kicker', 'TRACEABILITE'),
    tPdf('diagnostic.pdf_documents', 'Documents analyses'),
    tPdf('diagnostic.pdf_documents_subtitle', 'Source principale ayant servi au diagnostic')
  );
  drawTable(
    [
      tPdf('diagnostic.pdf_table_document', 'Document'),
      tPdf('diagnostic.pdf_table_company', 'Entreprise'),
      tPdf('diagnostic.pdf_table_model', 'Modele'),
      tPdf('diagnostic.pdf_table_approach', 'Approche')
    ],
    [[
      sourceFileName,
      meta.entreprise || tPdf('diagnostic.pdf_not_specified', 'Non specifie'),
      meta.modele_utilise || tPdf('diagnostic.pdf_not_specified', 'Non specifie'),
      meta.approche || tPdf('diagnostic.pdf_not_specified', 'Non specifie')
    ]],
    [58, 46, 42, 36]
  );

  if (questionsUsed.length > 0) {
    drawSectionTitle(
      tPdf('diagnostic.pdf_questions_kicker', 'PARAMETRAGE'),
      tPdf('diagnostic.pdf_questions_used', 'Questions utilisees'),
      tPdf('diagnostic.pdf_questions_subtitle', 'Questions ayant guide l extraction de ce rapport')
    );
    questionsUsed.slice(0, 8).forEach((question, index) => {
      drawWrapped(`${index + 1}. ${question}`, margin, 9.5, colors.text, 1.5, contentWidth, 'normal', 4.5);
    });
  }

  pdf.addPage();
  y = topContentY;
  drawSectionTitle(
    tPdf('diagnostic.pdf_reco_kicker', 'ACTIONS PRIORITAIRES'),
    tPdf('diagnostic.pdf_recommendations', 'Recommandations IA'),
    tPdf('diagnostic.pdf_reco_subtitle', 'Plan d action cible pour ameliorer la qualite documentaire')
  );

  if (recommendations.length > 0) {
    recommendations.forEach((rec, index) => {
      drawRecommendationCard(rec, index);
    });
  } else {
    drawWrapped(
      tPdf('diagnostic.pdf_reco_none', 'Aucune recommandation automatique n a ete generee pour cette extraction.'),
      margin,
      10,
      colors.muted,
      4
    );
  }

  if (metrics.missingLabels.length > 0) {
    drawSectionTitle(
      tPdf('diagnostic.pdf_missing_kicker', 'POINTS A COMPLETER'),
      tPdf('diagnostic.pdf_missing_title', 'Informations a consolider'),
      tPdf('diagnostic.pdf_missing_subtitle', 'Champs insuffisamment renseignes ou a confiance trop faible')
    );
    drawTable(
      [tPdf('diagnostic.pdf_table_missing', 'Champ a renforcer')],
      metrics.missingLabels.slice(0, 10).map((label) => [label]),
      [contentWidth]
    );
  }

  metrics.sectionStats
    .filter((section) => section.fieldCount > 0)
    .forEach((section) => {
      pdf.addPage();
      y = topContentY;
      drawSectionTitle(
        tPdf('diagnostic.pdf_detail_kicker', 'ANALYSE DETAILLEE'),
        section.title,
        tPdf(
          'diagnostic.pdf_detail_subtitle',
          'Champs extraits, niveau de confiance et references source'
        )
      );

      drawWrapped(
        tPdf(
          'diagnostic.pdf_detail_summary',
          'Couverture fiable: {filled}/{total} champs · Confiance moyenne: {confidence}%',
          {
            filled: section.filledCount,
            total: section.fieldCount,
            confidence: Math.round(section.avgConfidence)
          }
        ),
        margin,
        10,
        colors.muted,
        4
      );

      const rows = Object.keys(section.data).map((fieldKey) => {
        const fieldData = section.data[fieldKey];
        const page = fieldData && fieldData.source && fieldData.source.page != null
          ? `${tPdf('diagnostic.pdf_page_short', 'p.')} ${fieldData.source.page}`
          : tPdf('diagnostic.pdf_not_specified', 'Non specifie');
        const excerpt = fieldData && fieldData.source && fieldData.source.extrait
          ? ` · ${shortenText(fieldData.source.extrait, 80)}`
          : '';
        return [
          labelFromKey(fieldKey),
          fieldToText(fieldData),
          `${Math.round(getFieldConfidence(fieldData) * 100)}%`,
          `${page}${excerpt}`
        ];
      });

      drawTable(
        [
          tPdf('diagnostic.pdf_table_field', 'Champ'),
          tPdf('diagnostic.pdf_table_value', 'Valeur'),
          tPdf('diagnostic.pdf_table_confidence', 'Confiance'),
          tPdf('diagnostic.pdf_table_source', 'Source')
        ],
        rows,
        [34, 70, 22, 56]
      );
    });

  pdf.addPage();
  y = topContentY;
  drawSectionTitle(
    tPdf('diagnostic.pdf_conclusion_kicker', 'CLOTURE'),
    tPdf('diagnostic.pdf_conclusion', 'Conclusion'),
    tPdf('diagnostic.pdf_conclusion_subtitle', 'Synthese finale et signature automatique')
  );
  drawWrapped(
    tPdf(
      'diagnostic.pdf_conclusion_text',
      'Le diagnostic met en evidence un niveau de qualite documentaire de {quality}% avec une completude de {completeness}% et une confiance moyenne de {confidence}%. Les recommandations formulees permettent de prioriser les actions necessaires pour renforcer la conformite, la traçabilite et la completude des informations.',
      {
        quality: Math.round(metrics.quality),
        completeness: Math.round(metrics.completeness),
        confidence: Math.round(metrics.avgConfidence)
      }
    ),
    margin,
    10.5,
    colors.text,
    5
  );

  pdf.setFillColor(colors.paleBlue[0], colors.paleBlue[1], colors.paleBlue[2]);
  pdf.setDrawColor(colors.border[0], colors.border[1], colors.border[2]);
  pdf.roundedRect(margin, y, contentWidth, 28, 4, 4, 'FD');
  pdf.setFont('helvetica', 'bold');
  pdf.setFontSize(10.5);
  pdf.setTextColor(colors.navy[0], colors.navy[1], colors.navy[2]);
  pdf.text(cleanPdfText(tPdf('diagnostic.pdf_signature_title', 'Signature automatique')), margin + 5, y + 9);
  pdf.setFont('helvetica', 'normal');
  pdf.setFontSize(9.5);
  pdf.setTextColor(colors.text[0], colors.text[1], colors.text[2]);
  pdf.text(
    cleanPdfText(tPdf('diagnostic.pdf_signature_text', 'Rapport genere automatiquement par le Copilot IA Holokia. Aucune modification manuelle.')),
    margin + 5,
    y + 17
  );

  finalizeDocument();

  pdf.save(getExportFileName(data));
}

function buildCards(data) {
  cardsGrid.innerHTML = '';

  const recs = Array.isArray(data && data.recommandations) ? data.recommandations : [];
  if (recs.length > 0) {
    let recHtml = `
      <div style="grid-column: 1 / -1; background:var(--paper-2); border:1px solid var(--line); padding:24px;">
        <h3 style="font-family:var(--display); font-size:24px; margin-bottom:12px;">${tr('diagnostic.actions_title')}</h3>
        <div style="font-family:var(--mono); font-size:11px; color:var(--muted); margin-bottom:16px;">${tr('diagnostic.actions_subtitle')}</div>
        <ol style="margin:0; padding-left:18px; display:flex; flex-direction:column; gap:12px;">
    `;
    recs.slice(0, 3).forEach((r) => {
      const title = r && r.titre ? String(r.titre) : 'Action';
      const action = r && r.action ? String(r.action) : '';
      const reason = r && r.raison ? String(r.raison) : '';
      const cat = r && r.categorie ? String(r.categorie) : '';
      recHtml += `
        <li>
          <div style="font-family:var(--mono); font-size:10px; color:var(--muted); margin-bottom:4px; text-transform:uppercase; letter-spacing:0.5px;">${cat}${reason ? ` • ${reason}` : ''}</div>
          <div style="font-size:14px; color:var(--ink); font-weight:600; margin-bottom:4px;">${title}</div>
          <div style="font-size:13px; color:var(--ink-2); line-height:1.5;">${action}</div>
        </li>
      `;
    });
    recHtml += `</ol></div>`;
    cardsGrid.innerHTML += recHtml;
  }
  
  const sections = [
    { key: 'diagnostic_strategique', title: 'Stratégique' },
    { key: 'diagnostic_financier', title: 'Financier' },
    { key: 'diagnostic_rh', title: 'RH' },
    { key: 'diagnostic_data', title: 'Maturité Data' },
    { key: 'diagnostic_cyber_gouvernance', title: 'Cyber & Gouvernance' }
  ];

  sections.forEach((sec) => {
    const sectionData = data[sec.key] || {};
    const fields = Object.keys(sectionData);
    
    // Check if at least one field has a value
    const hasData = fields.some(f => {
      const fieldData = sectionData[f];
      if(!fieldData) return false;
      if(Array.isArray(fieldData.valeur)) return fieldData.valeur.length > 0;
      return fieldData.valeur !== null && fieldData.valeur !== undefined && String(fieldData.valeur).trim() !== '';
    });

    let html = `
      <div style="background:var(--paper-2); border:1px solid var(--line); padding:24px;">
        <h3 style="font-family:var(--display); font-size:24px; margin-bottom:16px; display:flex; justify-content:space-between;">
          ${sec.title}
          <span style="font-family:var(--mono); font-size:12px; color:${hasData ? 'var(--green)' : 'var(--red)'};">
            ${hasData ? tr('diagnostic.data_found') : tr('diagnostic.not_found')}
          </span>
        </h3>
        <div style="display:flex; flex-direction:column; gap:12px;">
    `;

    fields.forEach(f => {
      const fieldData = sectionData[f];
      const label = f.replace(/_/g, ' ').toUpperCase();
      let value = `<span style="color:var(--muted); font-style:italic;">${tr('common.not_specified')}</span>`;
      let sourceHtml = '';

      if (fieldData) {
        const isFound = Array.isArray(fieldData.valeur) 
          ? fieldData.valeur.length > 0 
          : (fieldData.valeur !== null && fieldData.valeur !== undefined && String(fieldData.valeur).trim() !== '');

        if (isFound) {
          if (Array.isArray(fieldData.valeur)) {
            // Affichage en tags pour les listes
            value = `<div style="display:flex; flex-wrap:wrap; gap:6px; margin-top:6px;">` + 
                    fieldData.valeur.map(v => `<span style="background:var(--paper); border:1px solid var(--line); padding:4px 8px; border-radius:4px; font-size:12px; color:var(--ink);">${v}</span>`).join('') + 
                    `</div>`;
          } else {
            let textVal = String(fieldData.valeur);
            if (textVal.length > 100) {
              // Affichage sous forme de paragraphe lisible pour les textes longs
              value = `<div style="color:var(--ink); font-weight:400; line-height:1.6; font-size:13px; background:var(--glass); padding:12px; border-radius:6px; border:1px solid var(--line); margin-top:6px; text-align:justify;">${textVal}</div>`;
            } else {
              // Affichage classique pour les textes courts
              value = `<strong style="color:var(--ink); font-weight:500; font-size:14px;">${textVal}</strong>`;
            }
          }
        }

        if (fieldData.source && fieldData.source.extrait) {
          sourceHtml = `
            <div style="margin-top:10px; padding:10px 14px; background:rgba(60,87,243,0.12); border-left:3px solid var(--blue); border-radius:0 6px 6px 0; font-size:11px; color:var(--muted); line-height:1.5;">
              <div style="font-family:var(--mono); color:var(--blue); font-weight:500; margin-bottom:6px; display:flex; align-items:center; gap:6px;">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
                ${tr('common.source').toUpperCase()} • ${tr('common.page').toUpperCase()} ${fieldData.source.page}
              </div>
              <div style="font-style:italic; opacity:0.9;">"${fieldData.source.extrait}"</div>
            </div>
          `;
        }
      }

      html += `
        <div style="border-bottom:1px solid rgba(10,10,10,0.05); padding-bottom:12px; margin-bottom:12px;">
          <div style="font-family:var(--mono); font-size:10px; color:var(--muted); margin-bottom:4px; text-transform:uppercase; letter-spacing:0.5px;">${label}</div>
          <div style="font-size:14px; line-height:1.4;">${value}</div>
          ${sourceHtml}
        </div>
      `;
    });

    html += `</div></div>`;
    cardsGrid.innerHTML += html;
  });

  // T8.26 : Afficher les questions utilisées si présentes
  if (data.meta && data.meta.questions_utilisees && data.meta.questions_utilisees.length > 0) {
    let qHtml = `
      <div style="grid-column: 1 / -1; background:var(--paper-3); border:1px solid var(--line); padding:24px; margin-top: 10px;">
        <h3 style="font-family:var(--display); font-size:20px; margin-bottom:16px;">${tr('diagnostic.questions_used')}</h3>
        <ul style="margin: 0; padding-left: 20px; font-size: 13px; color: var(--ink); line-height: 1.6;">
    `;
    data.meta.questions_utilisees.forEach(q => {
      qHtml += `<li><strong>${q.champ}</strong> : ${q.question}</li>`;
    });
    qHtml += `</ul></div>`;
    cardsGrid.innerHTML += qHtml;
  }
}

let pollInterval;

function setFormLocked(isLocked) {
  if (modelSelect) modelSelect.disabled = isLocked;
  if (approachSelect) approachSelect.disabled = isLocked;
}

function setStored(key, value) {
  try {
    if (value === undefined || value === null) {
      localStorage.removeItem(key);
    } else {
      localStorage.setItem(key, String(value));
    }
  } catch (_) {}
}

function resolveDiagnosticModelSelection(selectedModel) {
  if (selectedModel === 'gpt-4o' || selectedModel === 'openai') {
    return { provider: 'openai', model: 'gpt-4o' };
  }
  if (selectedModel === 'llama-3.3-70b-versatile') {
    return { provider: 'groq', model: 'llama-3.3-70b-versatile' };
  }
  if (selectedModel === 'qwen3:8b') {
    return { provider: 'ollama', model: 'qwen3:8b' };
  }
  if (selectedModel === 'groq') {
    return { provider: 'groq', model: 'llama-3.1-8b-instant' };
  }
  return { provider: 'ollama', model: selectedModel };
}

function getStored(key) {
  try {
    return localStorage.getItem(key);
  } catch (_) {
    return null;
  }
}

function setStoredJson(key, obj) {
  try {
    if (obj === undefined || obj === null) {
      localStorage.removeItem(key);
    } else {
      localStorage.setItem(key, JSON.stringify(obj));
    }
  } catch (_) {}
}

function getStoredJson(key) {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch (_) {
    return null;
  }
}

btnExtract.addEventListener('click', async () => {
  if(!fileInput.files[0]) {
    alert(tr('diagnostic.pick_file'));
    return;
  }

  if (pollInterval) {
    clearTimeout(pollInterval);
    pollInterval = undefined;
  }

  btnExtract.disabled = true;
  setFormLocked(true);
  btnExtract.textContent = tr('diagnostic.processing_btn');
  statusText.style.display = "block";
  statusText.textContent = tr('diagnostic.sending_status');
  setStored("holokia_processing", "1");
  setStored("holokia_status", statusText.textContent);
  setStored("holokia_hash", "#demo");
  resultsSection.style.display = "none";

  const fd = new FormData();
  fd.append('file', fileInput.files[0]);
  
  const selectedModel = modelSelect.value;
  const selection = resolveDiagnosticModelSelection(selectedModel);
  const provider = selection.provider;
  const model = selection.model;
  
  fd.append('provider', provider);
  if(model) fd.append('model', model);
  fd.append('approach', approachSelect ? approachSelect.value : 'agent');
  
  const isAsync = document.querySelector('input[name="asyncMode"]:checked').value === "true";
  fd.append('async_mode', isAsync);
  setStored("holokia_async", isAsync ? "1" : "0");

  try {
    const response = await Auth.apiFetch(`${API_URL}/extract`, {
      method: 'POST',
      body: fd
    });
    
    const data = await response.json();
    
    if (isAsync && data.job_id) {
      statusText.textContent = tr('diagnostic.job_created', { jobId: data.job_id });
      setStored("holokia_job_id", data.job_id);
      setStored("holokia_status", statusText.textContent);
      pollJobStatus(data.job_id);
    } else {
      showResults(data);
    }
  } catch(e) {
    statusText.textContent = tr('diagnostic.server_unreachable');
    btnExtract.disabled = false;
    setFormLocked(false);
    btnExtract.textContent = tr('diagnostic.extract_btn');
    setStored("holokia_processing", "0");
    setStored("holokia_job_id", null);
    setStored("holokia_status", statusText.textContent);
  }
});

async function pollJobStatus(jobId) {
  let delay = 800;
  let failures = 0;
  const tick = async () => {
    try {
      const res = await Auth.apiFetch(`${API_URL}/status/${jobId}`);
      if (!res.ok) {
        let text = "";
        try {
          text = await res.text();
        } catch (_) {}
        throw { status: res.status, text };
      }
      const data = await res.json();
      
      if (data.status === "completed") {
        pollInterval = undefined;
        showResults(data.result);
      } else if (data.status === "failed") {
        pollInterval = undefined;
        statusText.textContent = `Erreur: ${data.error}`;
        btnExtract.disabled = false;
        setFormLocked(false);
        btnExtract.textContent = tr('diagnostic.extract_btn');
        setStored("holokia_processing", "0");
        setStored("holokia_job_id", null);
        setStored("holokia_status", statusText.textContent);
      } else {
        failures = 0;
        const statusUpper = data.status.toUpperCase();
        let extra = "";
        if (data.status === "queued") extra = tr('diagnostic.queued_extra');
        else if (data.status === "processing") extra = tr('diagnostic.processing_extra');
        statusText.textContent = `Statut: ${statusUpper}${extra}`;
        setStored("holokia_status", statusText.textContent);
        delay = Math.min(2000, Math.round(delay * 1.1));
        pollInterval = window.setTimeout(tick, delay);
      }
    } catch(e) {
      failures += 1;
      const status = e && typeof e === "object" ? e.status : undefined;
      const retriable = status === 502 || status === 503 || status === 504;
      if (retriable && failures <= 12) {
        delay = Math.min(8000, Math.round(delay * 1.4) + 200);
        const seconds = Math.max(1, Math.round(delay / 1000));
        statusText.textContent = tr('diagnostic.server_busy', { status, seconds });
        setStored("holokia_status", statusText.textContent);
        pollInterval = window.setTimeout(tick, delay);
        return;
      }

      pollInterval = undefined;
      statusText.textContent = tr('diagnostic.job_status_error');
      btnExtract.disabled = false;
      setFormLocked(false);
      btnExtract.textContent = tr('diagnostic.extract_btn');
      setStored("holokia_processing", "0");
      setStored("holokia_job_id", null);
      setStored("holokia_status", statusText.textContent);
    }
  };

  if (pollInterval) {
    clearTimeout(pollInterval);
  }
  pollInterval = window.setTimeout(tick, delay);
}

function showResults(data, options) {
  const scroll = !(options && options.scroll === false);
  let statusMsg = tr('diagnostic.completed');
  if (data && data.storage) {
    if (data.storage.extraction_id) {
      statusMsg += tr('diagnostic.history_saved');
    } else if (data.storage.supabase_enabled && data.storage.error) {
      statusMsg += tr('diagnostic.history_error', { error: data.storage.error });
    } else if (data.storage.supabase_enabled) {
      statusMsg += tr('diagnostic.history_not_saved');
    }
  }
  statusText.textContent = statusMsg;
  setStored("holokia_status", statusText.textContent);
  setStored("holokia_processing", "0");
  setStored("holokia_job_id", null);
  
  // Retrait de la gestion du hash "#results"
  // setStored("holokia_hash", "#results");
  // if (location.hash !== "#results") {
  //   location.hash = "#results";
  // }
  
  // Appel de la nouvelle fonction pour générer les cartes visuelles
  buildCards(data);

  // Garder le JSON brut mais formatté pour la section développeur
  jsonOutput.textContent = JSON.stringify(data, null, 2);
  setStoredJson("holokia_last_result", data);
  
  resultsSection.style.display = "block";
  if (scroll) {
    resultsSection.scrollIntoView({behavior: 'smooth'});
  }
  btnExtract.disabled = false;
  setFormLocked(false);
  btnExtract.textContent = tr('diagnostic.extract_btn');
}

btnCopy.addEventListener('click', () => {
  navigator.clipboard.writeText(jsonOutput.textContent).then(() => {
    const oldText = btnCopy.textContent;
    btnCopy.textContent = tr('common.copied');
    setTimeout(() => btnCopy.textContent = oldText, 2000);
  });
});

if (btnExportPdf) {
  btnExportPdf.addEventListener('click', async () => {
    const current = getStoredJson("holokia_last_result");
    await exportDiagnosticPdf(current);
  });
}

(() => {
  const storedStatus = getStored("holokia_status");
  if (storedStatus) {
    statusText.style.display = "block";
    statusText.textContent = storedStatus;
  }
  const isProcessing = getStored("holokia_processing") === "1";
  const jobId = getStored("holokia_job_id");
  const lastResult = getStoredJson("holokia_last_result");

  if (isProcessing && jobId) {
    btnExtract.disabled = true;
    setFormLocked(true);
    btnExtract.textContent = tr('diagnostic.processing_btn');
    resultsSection.style.display = "none";
    pollJobStatus(jobId);
    return;
  }

  // Restaurer le dernier résultat s'il existe
  if (lastResult && !isProcessing) {
    // Afficher les résultats précédents sans faire défiler la page
    buildCards(lastResult);
    jsonOutput.textContent = JSON.stringify(lastResult, null, 2);
    resultsSection.style.display = "block";
  } else {
    // On s'assure que la section résultats est bien cachée au démarrage
    resultsSection.style.display = "none";
  }
})();

// ==========================================
// T8.22 - PANNEAU LATÉRAL "MES QUESTIONS"
// ==========================================
const btnOpenQuestions = document.getElementById('btnOpenQuestions');
const btnCloseQuestions = document.getElementById('btnCloseQuestions');
const questionsPanel = document.getElementById('questionsPanel');
const questionsOverlay = document.getElementById('questionsOverlay');
const questionsList = document.getElementById('questionsList');
const addQuestionForm = document.getElementById('addQuestionForm');
const btnResetQuestions = document.getElementById('btnResetQuestions');

function toggleQuestionsPanel(show) {
  if (show) {
    questionsOverlay.style.display = 'block';
    setTimeout(() => {
      questionsOverlay.style.opacity = '1';
      questionsPanel.style.right = '0';
    }, 10);
    loadQuestions();
  } else {
    questionsOverlay.style.opacity = '0';
    questionsPanel.style.right = '-450px';
    setTimeout(() => {
      questionsOverlay.style.display = 'none';
    }, 300);
  }
}

if (btnOpenQuestions) btnOpenQuestions.addEventListener('click', () => toggleQuestionsPanel(true));
if (btnCloseQuestions) btnCloseQuestions.addEventListener('click', () => toggleQuestionsPanel(false));
if (questionsOverlay) questionsOverlay.addEventListener('click', () => toggleQuestionsPanel(false));

async function loadQuestions() {
  questionsList.innerHTML = `<div style="text-align:center; font-family:var(--mono); font-size:12px; color:var(--muted);">${tr('diagnostic.loading_questions')}</div>`;
  try {
    const res = await Auth.apiFetch(`${API_URL}/questions`);
    const data = await res.json();
    if (!data.ok) throw new Error(data.error || tr('common.error'));
    
    // Grouper par catégorie
    const grouped = {};
    data.data.forEach(q => {
      if (!grouped[q.categorie]) grouped[q.categorie] = [];
      grouped[q.categorie].push(q);
    });
    
    if (Object.keys(grouped).length === 0) {
      questionsList.innerHTML = `<div style="text-align:center; font-family:var(--mono); font-size:12px; color:var(--muted);">${tr('diagnostic.no_questions')}</div>`;
      return;
    }
    
    let html = '';
    for (const [cat, qs] of Object.entries(grouped)) {
      html += `<div style="margin-bottom:20px;">
        <div style="font-family:var(--mono); font-size:11px; color:var(--blue); margin-bottom:10px; text-transform:uppercase; border-bottom:1px solid var(--line); padding-bottom:5px;">${cat}</div>
        <div style="display:flex; flex-direction:column; gap:10px;">
      `;
      qs.forEach(q => {
        const isDef = q.is_default ? '<span style="font-size:9px; background:var(--glass); border:1px solid var(--line); padding:2px 4px; border-radius:3px;">Défaut</span>' : '<span style="font-size:9px; background:rgba(60,87,243,0.20); color:var(--blue); padding:2px 4px; border-radius:3px;">Personnalisée</span>';
        html += `
          <div style="border:1px solid var(--line); padding:10px; border-radius:4px; font-size:12px; position:relative;">
            <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
              <strong style="font-family:var(--mono); font-size:11px;">${q.champ}</strong>
              ${isDef}
            </div>
            <div style="color:var(--ink); line-height:1.4;">${q.question_text}</div>
            <div style="margin-top:8px; text-align:right;">
              <button onclick="deleteQuestion('${q.id}')" style="background:none; border:none; color:var(--red); font-size:11px; cursor:pointer; font-family:var(--mono);">${tr('common.delete')}</button>
            </div>
          </div>
        `;
      });
      html += `</div></div>`;
    }
    questionsList.innerHTML = html;
  } catch (e) {
    questionsList.innerHTML = `<div style="color:var(--red); font-size:12px;">${tr('common.error')}: ${e.message}</div>`;
  }
}

if (addQuestionForm) {
  addQuestionForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = addQuestionForm.querySelector('button');
    btn.textContent = tr('diagnostic.adding');
    btn.disabled = true;
    
    try {
      const payload = {
        categorie: document.getElementById('qCategory').value,
        champ: document.getElementById('qChamp').value,
        question_text: document.getElementById('qText').value,
        type: document.getElementById('qType').value
      };
      
      const res = await Auth.apiFetch(`${API_URL}/questions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (!data.ok) throw new Error(data.error);
      
      addQuestionForm.reset();
      await loadQuestions();
    } catch (err) {
      alert(`${tr('common.error')}: ${err.message}`);
    } finally {
      btn.textContent = tr('diagnostic.add_btn');
      btn.disabled = false;
    }
  });
}

async function deleteQuestion(id) {
  if (!confirm(tr('diagnostic.confirm_delete_question'))) return;
  try {
    const res = await Auth.apiFetch(`${API_URL}/questions/${id}`, { method: 'DELETE' });
    const data = await res.json();
    if (!data.ok) throw new Error(data.error);
    await loadQuestions();
  } catch (err) {
    alert(`${tr('common.error')}: ${err.message}`);
  }
}

if (btnResetQuestions) {
  btnResetQuestions.addEventListener('click', async () => {
    if (!confirm(tr('diagnostic.confirm_reset_questions'))) return;
    btnResetQuestions.textContent = tr('diagnostic.resetting');
    try {
      const res = await Auth.apiFetch(`${API_URL}/questions/reset`, { method: 'POST' });
      const data = await res.json();
      if (!data.ok) throw new Error(data.error);
      await loadQuestions();
    } catch (err) {
      alert(`${tr('common.error')}: ${err.message}`);
    } finally {
      btnResetQuestions.textContent = tr('diagnostic.reset_defaults');
    }
  });
}

document.addEventListener('i18n:updated', () => {
  const lastResult = getStoredJson("holokia_last_result");
  if (lastResult) {
    buildCards(lastResult);
  }
  if (btnCopy) btnCopy.textContent = tr('common.copy');
  if (btnExportPdf) btnExportPdf.textContent = tr('common.export_pdf');
  const isProcessing = getStored("holokia_processing") === "1";
  if (!isProcessing && btnExtract) {
    btnExtract.textContent = tr('diagnostic.extract_btn');
  }
  if (questionsOverlay && questionsOverlay.style.display === 'block') {
    loadQuestions();
  }
});
