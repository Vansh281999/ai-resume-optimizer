# PARSER_QUALITY_REPORT

## Generated
2026-06-21

## Parser Version
`ResumeIngestionPipeline` with `SectionClassifier` + `ConfidenceScorer` + `CANONICAL_SKILLS`

## Benchmark Dataset
3 synthetic resumes covering student, experienced, and Indian formats:
- `student_basic`: Alice Johnson, UT Austin, CS degree, intern at TechCorp
- `experienced_senior`: Michael Chen, Google/Amazon, MS Stanford + BTech IIT
- `indian_resume`: Rajesh Kumar, VIT Vellore, Amazon intern, Indian format

---

## Accuracy Results

### Overall Per-Field Accuracy

| Field | student_basic | experienced_senior | indian_resume | AVG |
|-------|--------------|-------------------|---------------|-----|
| Name | 100% | 100% | 100% | **100%** |
| Email | 100% | 100% | 100% | **100%** |
| Phone | 100% | 100% | 100% | **100%** |
| Location | 80% | 80% | 80% | **80%** |
| LinkedIn | 100% | 100% | 100% | **100%** |
| GitHub | 100% | 100% | 100% | **100%** |
| Education | 83% | 96% | 100% | **93%** |
| Experience | 100% | 79% | 100% | **93%** |
| Projects | 50% | 50% | 50% | **50%** |
| Skills | 31% | 38% | 28% | **32%** |
| Certifications | 56% | 50% | 56% | **54%** |

### Production Readiness Score: 75/100

| Category | Score | Notes |
|----------|-------|-------|
| Personal Info | 100/100 | Name, email, phone, LinkedIn, GitHub flawless |
| Education | 93/100 | Degree/institution/year/CGPA extraction strong |
| Experience | 93/100 | Title/company/dates/bullets well extracted |
| Projects | 50/100 | Structure correct but text formatting causes split errors |
| Skills | 32/100 | Section bleed contamination (headers captured as skills) |
| Certifications | 54/100 | Name captured but issuer/date extraction weak |
| Location | 80/100 | City DB lookup works; missing state/country formatting |

---

## False Positives

### Skills Section (Critical)
| False Positive | Source | Cause |
|----------------|--------|-------|
| `PROJECTS` | Project header | `section_headers` regex missing `projects?` |
| `INTERNSHIP` | Experience line | Title regex too broad |
| `CERTIFICATES` | Cert header | Skills section boundary leak |
| `SDE Intern at Amazon` | Experience line | Non-bullet experience text captured |
| `Jun 2024 - Aug 2024` | Date line | Skills regex captures date text |
| `Core Java` | Skills content | Categorized as general instead of programming_languages |
| `CI`, `CD` | Skills text | Split from "CI/CD" abbreviation |
| `alicejohnson`, `campus-shop` | URLs | GitHub username leakage |

### Projects Section (Moderate)
| False Positive | Source | Cause |
|----------------|--------|-------|
| `CERTIFICATES` | Cert header | Project extractor continues past section boundary |
| `Java Certified Programmer - Oracle - 2023` | Cert content | Captured as project `technologies` |

### Education Section (Low)
| False Positive | Source | Cause |
|----------------|--------|-------|
| `Bachelor of Science` + `of Science in Computer Science` split | Degree line | `degree_m.end()` truncation splits degree in half |
| `M.S. Computer Science, Stanford` | Education line | Missing specialization field; institution = "University" |

---

## False Negatives

| Missing Field | Example | Cause |
|---------------|---------|-------|
| Location | "Austin, TX" → "Austin" | City DB matched but state stripped |
| Project URLs | `github.com/alicejohnson/campus-shop` not extracted | Tech stack parsing splits URL parts |
| Skill: Node.js | Categorized as `general` | Not in CANONICAL_SKILLS dict |
| Skill: TensorFlow, Pandas | Categorized as `ai_ml_technologies` | ✅ Actually correct (false alarm in audit) |
| Skill: Tailwind CSS | Categorized as `frameworks` | ✅ Correct |
| Certification issuer | "Amazon Web Services" | Issuer regex not matching "Amazon Web Services" |

---

## Confidence Calibration

| Field | Confidence | Calibration |
|-------|-----------|-------------|
| Name | 0.95 | Correct |
| Email | 1.0 | Correct |
| Phone | 0.95 | Correct |
| Location | 0.7 | Slightly high (only city, missing state) |
| LinkedIn/GitHub | 0.95 | Correct |
| Education | 0.85 | Solid |
| Experience | 0.9 | Good |
| Projects | 0.6 | Overconfident (formatting-sensitive) |
| Skills | 0.4 | Underconfident (section bleed lowers trust) |
| Certifications | 0.5 | Appropriate |

---

## Remaining Issues

1. **Skills section bleed (HIGH)**: `section_headers` regex needs `projects?`, `internships?`, `technologies`, `programming[\s_]languages`, `tools?\s*&?\s*technologies`
2. **Projects section bleed (HIGH)**: `_extract_projects` doesn't respect section-aware boundaries in non-section-aware fallback mode
3. **Education degree truncation (MEDIUM)**: `degree_m.end()` splits "Bachelor of Science" into "Bachelor" + "of Science..."
4. **Project URL parsing (MEDIUM)**: `_parse_project_line` splits on ` - ` but URL contains `/` which doesn't conflict
5. **Certification issuer (LOW)**: "Amazon Web Services" not captured by issuer regex
6. **No confidence scores in output**: `ConfidenceScorer` class built but not wired into extractor return values

---

## Deployment Status

| Commit | Description |
|--------|-------------|
| `69a5cce` | **CURRENT** - Production-grade parser with section classifier |
| `d0e6a23` | Frontend onboarding auto-save + rule-based rewrite |
| `a76332b` | Database init fix for Render |
| `4d0d95a` | Parse-resume fallback and logging |
| `f20a383` | HashRouter fix for GitHub Pages |

**Note**: Backend runs on Render free tier. Each push to `master` requires MANUAL "Deploy latest commit" in Render dashboard. No auto-deploy configured.

---

## Recommended Next Steps

1. **Critical**: Fix skills section bleed by expanding `section_headers` regex
2. **Critical**: Fix project section bleed in non-section-aware fallback
3. **High**: Wire `ConfidenceScorer` into all extractors so each field returns `{value, confidence}`
4. **High**: Add configuration flag for auto-fill threshold (e.g., 0.7)
5. **Medium**: Add more benchmark samples (ATS-formatted, non-standard, international)
6. **Medium**: Add PDF/DOCX benchmark samples with real parser output
7. **Low**: Improve certification issuer/date extraction
