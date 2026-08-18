const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  BorderStyle, LevelFormat, convertInchesToTwip, ExternalHyperlink,
  PositionalTab, PositionalTabAlignment, PositionalTabLeader, PositionalTabRelativeTo,
} = require("docx");
const fs = require("fs");

const NAVY = "1B2A4A";
const DARKGRAY = "222222";
const MIDGRAY = "444444";

function sectionHeading(text) {
  return new Paragraph({
    spacing: { before: 240, after: 100 },
    border: { bottom: { color: NAVY, space: 2, style: BorderStyle.SINGLE, size: 6 } },
    children: [
      new TextRun({ text, bold: true, size: 21, color: NAVY, allCaps: true, font: "Calibri" }),
    ],
  });
}

function entryHeader(leftText, rightText) {
  return new Paragraph({
    tabStops: [{ type: "right", position: convertInchesToTwip(6.5) }],
    spacing: { after: 20 },
    children: [
      new TextRun({ text: leftText, bold: true, size: 21, color: DARKGRAY, font: "Calibri" }),
      new TextRun({ text: "\t" + rightText, italics: true, size: 20, color: MIDGRAY, font: "Calibri" }),
    ],
  });
}

function subLine(text) {
  return new Paragraph({
    spacing: { after: 80 },
    children: [new TextRun({ text, italics: true, size: 20, color: MIDGRAY, font: "Calibri" })],
  });
}

function bullet(text, boldLead) {
  const runs = [];
  if (boldLead) {
    runs.push(new TextRun({ text: boldLead, bold: true, size: 20, font: "Calibri", color: DARKGRAY }));
    runs.push(new TextRun({ text: text, size: 20, font: "Calibri", color: DARKGRAY }));
  } else {
    runs.push(new TextRun({ text, size: 20, font: "Calibri", color: DARKGRAY }));
  }
  return new Paragraph({
    numbering: { reference: "bullet-list", level: 0 },
    spacing: { after: 40 },
    children: runs,
  });
}

const doc = new Document({
  numbering: {
    config: [{
      reference: "bullet-list",
      levels: [{
        level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: convertInchesToTwip(0.25), hanging: convertInchesToTwip(0.15) } } },
      }],
    }],
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 720, bottom: 720, left: 720, right: 720 },
      },
    },
    children: [
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 40 },
        children: [new TextRun({ text: "MAX DODSON", bold: true, size: 32, color: NAVY, font: "Calibri" })],
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 160 },
        children: [new TextRun({
          text: "Fayetteville, AR  |  maxhenrydodson@gmail.com  |  (214) 493-9282",
          size: 19, color: MIDGRAY, font: "Calibri",
        })],
      }),

      sectionHeading("Education"),
      entryHeader("University of Arkansas — Fayetteville, AR", "Expected December 2027"),
      subLine("Bachelor of Computer Science, Minor in Mathematics"),
      entryHeader("Washington University in St. Louis — St. Louis, MO", "2021–2023"),
      subLine("Architecture Studies"),
      entryHeader("The Odin Project — Fayetteville, AR", "2024"),
      subLine("Full Stack JavaScript Curriculum"),

      sectionHeading("Experience"),
      entryHeader("Data Analyst Contractor", "May 2024–December 2025"),
      subLine("Hedgerow: Environmental Health Software — Remote"),
      bullet("Analyzed operational data across 30+ projects and 300+ employees using Microsoft Power BI, identifying monthly and annual trends in labor hours, staffing, and project performance"),
      bullet("Cleaned and transformed 2,000+ raw timekeeping records into structured employee- and project-level datasets for analysis and reporting"),
      bullet("Built interactive Power BI reports and calculations to track project labor, staffing trends, and costs across monthly and annual reporting periods"),
      bullet("Presented data-driven insights and performance trends to company leadership, supporting project planning, workforce allocation, and budget decisions"),

      entryHeader("President / Volunteer Team Leader", "August 2025–Present"),
      subLine("Young Life — University of Arkansas — Fayetteville, AR"),
      bullet("Lead a 200-member university organization and directly manage a team of 8 volunteer leaders through task delegation, scheduling, weekly meetings, and ongoing performance check-ins"),
      bullet("Plan and execute weekly events for approximately 100 attendees, coordinating responsibilities across the leadership team and with full-time Northwest Arkansas staff"),
      bullet("Recruit and mentor student volunteers, helping connect individuals with service opportunities across Northwest Arkansas youth programs"),
      bullet("Deliver announcements and presentations to groups of 100+ students and lead recurring small-group discussions"),

      sectionHeading("Projects"),
      entryHeader("Studio Performance Analytics — Multi-Office BI Dashboard", "2026"),
      subLine("Python, SQL (SQLite), Data Modeling, ETL, Chart.js  |  [add live demo / GitHub link]"),
      bullet("Designed a 6-table relational data model and built a Python ETL pipeline to clean and load 6,500+ raw timekeeping records, resolving inconsistent date formats, duplicate entries, and invalid values into a 98%+ clean dataset"),
      bullet("Wrote analytical SQL to calculate staff utilization, project profitability/margin, and schedule performance across a simulated 220-employee, 7-office architecture & engineering firm spanning 72 projects"),
      bullet("Built an interactive dashboard with sortable, filterable project and staffing tables and utilization, margin, and schedule-risk visualizations to support leadership decision-making"),
      bullet("Independently scoped, built, and documented the full pipeline end-to-end, from schema design through a deployed, self-contained dashboard"),

      sectionHeading("Technical Skills"),
      new Paragraph({
        spacing: { after: 40 },
        children: [
          new TextRun({ text: "Data & Business Intelligence: ", bold: true, size: 20, font: "Calibri", color: DARKGRAY }),
          new TextRun({ text: "Microsoft Power BI, Excel, SQL, Data Visualization, Data Cleaning & Transformation, Business Reporting", size: 20, font: "Calibri", color: DARKGRAY }),
        ],
      }),
      new Paragraph({
        spacing: { after: 40 },
        children: [
          new TextRun({ text: "Programming: ", bold: true, size: 20, font: "Calibri", color: DARKGRAY }),
          new TextRun({ text: "R, JavaScript, Java, C++, HTML/CSS", size: 20, font: "Calibri", color: DARKGRAY }),
        ],
      }),
      new Paragraph({
        spacing: { after: 40 },
        children: [
          new TextRun({ text: "Tools: ", bold: true, size: 20, font: "Calibri", color: DARKGRAY }),
          new TextRun({ text: "Git, GitHub, Microsoft Office", size: 20, font: "Calibri", color: DARKGRAY }),
        ],
      }),
    ],
  }],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync("Max_Dodson_Resume.docx", buf);
  console.log("wrote Max_Dodson_Resume.docx");
});
