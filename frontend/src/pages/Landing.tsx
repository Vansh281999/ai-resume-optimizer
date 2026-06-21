import { ArrowRight, BarChart3, Briefcase, CheckCircle2, ChevronDown, ClipboardCheck, GraduationCap, LineChart, ShieldCheck, Sparkles, Target, Users } from 'lucide-react';
import { Link } from 'react-router-dom';

const features = [
  { icon: ClipboardCheck, title: 'ATS Resume Scoring', description: 'Score resumes against target keywords and identify missing sections before you apply.' },
  { icon: Briefcase, title: 'Job Match Intelligence', description: 'Compare your resume with job descriptions to reveal skill gaps and recommended keywords.' },
  { icon: GraduationCap, title: 'Interview Preparation', description: 'Generate technical, behavioral, and company-specific questions from real role context.' },
  { icon: LineChart, title: 'Career Analytics', description: 'Track score trends, match quality, and career readiness across your job search.' },
];

const pricing = [
  {
    name: 'Starter',
    price: '$19',
    description: 'For students and early-career applicants building momentum.',
    features: ['10 ATS scans per month', 'Job match analysis', 'Basic interview prep', 'Career roadmap generator'],
  },
  {
    name: 'Professional',
    price: '$39',
    description: 'For active job seekers optimizing every application.',
    features: ['Unlimited ATS scans', 'Advanced job matching', 'Priority interview questions', 'Analytics dashboard', 'Resume upload support'],
    highlighted: true,
  },
  {
    name: 'Team',
    price: '$99',
    description: 'For career centers, bootcamps, and hiring teams.',
    features: ['Team workspaces', 'Centralized reporting', 'Role-based access', 'Bulk resume reviews', 'Dedicated onboarding'],
  },
];

const faqs = [
  { question: 'Does the analyzer replace human resume review?', answer: 'No. It gives instant AI-powered feedback so you can improve your resume before asking a mentor, recruiter, or career coach for review.' },
  { question: 'Can I use the platform for different roles?', answer: 'Yes. Paste the target job description or keywords for each application and the platform tailors scoring, matching, and interview preparation.' },
  { question: 'Where is my data sent?', answer: 'The frontend calls the configured API at http://localhost:8000/api. Review your backend privacy policy before uploading sensitive documents.' },
  { question: 'What makes the job match useful?', answer: 'It separates skill match, experience match, missing skills, recommended keywords, and detailed reasoning so you know exactly what to improve.' },
];

export function Landing() {
  console.log('[PROD-DIAG] Landing rendered');
  return (
    <div className="overflow-hidden bg-slate-950 text-white">
      <header className="mx-auto flex max-w-7xl items-center justify-between px-6 py-6">
        <Link to="/" className="flex items-center gap-3">
          <div className="flex size-11 items-center justify-center rounded-2xl bg-primary-500 text-white shadow-glow">
            <Sparkles className="size-6" />
          </div>
          <span className="text-lg font-black">AI Career Platform</span>
        </Link>
        <div className="hidden items-center gap-8 md:flex">
          <a href="#features" className="text-sm font-semibold text-slate-300 transition hover:text-white">Features</a>
          <a href="#pricing" className="text-sm font-semibold text-slate-300 transition hover:text-white">Pricing</a>
          <a href="#faq" className="text-sm font-semibold text-slate-300 transition hover:text-white">FAQ</a>
          <Link to="/signup" className="rounded-2xl bg-white px-5 py-3 text-sm font-black text-slate-950 transition hover:bg-slate-200">Get started</Link>
        </div>
      </header>

      <section className="mx-auto grid max-w-7xl items-center gap-12 px-6 py-20 lg:grid-cols-2 lg:py-32">
        <div>
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/10 px-4 py-2 text-sm font-semibold text-slate-200 backdrop-blur">
            <ShieldCheck className="size-4 text-emerald-300" />
            Built for smarter career decisions
          </div>
          <h1 className="section-heading text-white">Optimize your resume, match better jobs, and prepare with confidence.</h1>
          <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-300">
            A complete AI career platform that scores resumes, compares them to job descriptions, generates interview prep, and maps your next career move.
          </p>
          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <Link to="/signup" className="btn-primary inline-flex">
              Start free today <ArrowRight className="size-4" />
            </Link>
            <Link to="/login" className="btn-secondary inline-flex border-white/10 bg-white/10 text-white hover:bg-white/20 dark:border-white/10 dark:bg-white/10 dark:text-white dark:hover:bg-white/20">
              Sign in
            </Link>
          </div>
          <div className="mt-10 grid max-w-xl grid-cols-3 gap-4">
            {[
              ['92%', 'average ATS lift'],
              ['4x', 'faster prep'],
              ['24/7', 'AI guidance'],
            ].map(([value, label]) => (
              <div key={label} className="rounded-3xl border border-white/10 bg-white/10 p-4 backdrop-blur">
                <p className="text-2xl font-black">{value}</p>
                <p className="mt-1 text-xs font-semibold uppercase tracking-wider text-slate-300">{label}</p>
              </div>
            ))}
          </div>
        </div>
        <div className="relative">
          <div className="absolute -inset-8 rounded-full bg-primary-500/30 blur-3xl"></div>
          <div className="relative rounded-[2rem] border border-white/10 bg-white/10 p-6 shadow-glow backdrop-blur">
            <div className="grid gap-4">
              {[
                ['ATS Score', 88, 'Missing: Certifications, Projects'],
                ['Job Match', 76, 'Add: Kubernetes, CI/CD'],
                ['Interview Readiness', 82, 'Practice: System design'],
              ].map(([label, score, detail]) => (
                <div key={label} className="rounded-3xl bg-slate-950/70 p-5">
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <p className="font-bold">{label}</p>
                      <p className="mt-1 text-sm text-slate-400">{detail}</p>
                    </div>
                    <div className="text-3xl font-black text-emerald-300">{score}%</div>
                  </div>
                  <div className="mt-4 h-3 overflow-hidden rounded-full bg-white/10">
                    <div className="h-full rounded-full bg-gradient-to-r from-primary-400 to-emerald-400" style={{ width: `${score}%` }}></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section id="features" className="mx-auto max-w-7xl px-6 py-20">
        <div className="mx-auto max-w-2xl text-center">
          <p className="text-sm font-black uppercase tracking-[0.25em] text-primary-300">Features</p>
          <h2 className="section-heading mt-3 text-white">Everything needed for a modern job search.</h2>
          <p className="mt-5 text-lg leading-8 text-slate-300">Move from resume upload to interview-ready with one connected workflow.</p>
        </div>
        <div className="mt-12 grid gap-5 md:grid-cols-2 lg:grid-cols-4">
          {features.map((feature) => (
            <div key={feature.title} className="rounded-3xl border border-white/10 bg-white/5 p-6 transition hover:-translate-y-1 hover:bg-white/10">
              <div className="mb-5 flex size-12 items-center justify-center rounded-2xl bg-primary-500 text-white">
                <feature.icon className="size-6" />
              </div>
              <h3 className="text-lg font-black">{feature.title}</h3>
              <p className="mt-3 leading-7 text-slate-300">{feature.description}</p>
            </div>
          ))}
        </div>
      </section>

      <section id="pricing" className="mx-auto max-w-7xl px-6 py-20">
        <div className="mx-auto max-w-2xl text-center">
          <p className="text-sm font-black uppercase tracking-[0.25em] text-primary-300">Pricing</p>
          <h2 className="section-heading mt-3 text-white">Plans that scale with your search.</h2>
        </div>
        <div className="mt-12 grid gap-6 lg:grid-cols-3">
          {pricing.map((plan) => (
            <div key={plan.name} className={[
              'relative rounded-[2rem] border p-8',
              plan.highlighted ? 'border-primary-400 bg-primary-500/15 shadow-glow' : 'border-white/10 bg-white/5',
            ].join(' ')}>
              {plan.highlighted && <span className="absolute right-6 top-6 rounded-full bg-emerald-400 px-3 py-1 text-xs font-black text-slate-950">Popular</span>}
              <h3 className="text-2xl font-black">{plan.name}</h3>
              <p className="mt-3 text-sm leading-7 text-slate-300">{plan.description}</p>
              <p className="mt-6 text-5xl font-black">{plan.price}<span className="text-sm font-bold text-slate-400">/mo</span></p>
              <ul className="mt-8 space-y-3">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex items-center gap-3 text-sm font-semibold text-slate-200">
                    <CheckCircle2 className="size-5 text-emerald-300" />
                    {feature}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </section>

      <section id="faq" className="mx-auto max-w-7xl px-6 py-20">
        <div className="grid gap-10 lg:grid-cols-[0.8fr_1.2fr]">
          <div>
            <p className="text-sm font-black uppercase tracking-[0.25em] text-primary-300">FAQ</p>
            <h2 className="section-heading mt-3 text-white">Answers for applicants and teams.</h2>
          </div>
          <div className="space-y-4">
            {faqs.map((faq) => (
              <details key={faq.question} className="group rounded-3xl border border-white/10 bg-white/5 p-6">
                <summary className="flex cursor-pointer list-none items-center justify-between gap-4 font-black">
                  {faq.question}
                  <ChevronDown className="size-5 shrink-0 transition group-open:rotate-180" />
                </summary>
                <p className="mt-4 leading-7 text-slate-300">{faq.answer}</p>
              </details>
            ))}
          </div>
        </div>
      </section>

      <footer className="border-t border-white/10 px-6 py-10">
        <div className="mx-auto flex max-w-7xl flex-col justify-between gap-6 md:flex-row md:items-center">
          <div className="flex items-center gap-3">
            <div className="flex size-10 items-center justify-center rounded-2xl bg-primary-500 text-white">
              <Sparkles className="size-5" />
            </div>
            <div>
              <p className="font-black">AI Career Platform</p>
              <p className="text-sm text-slate-400">Resume, job match, interview, and roadmap tools.</p>
            </div>
          </div>
          <div className="flex gap-6 text-sm font-semibold text-slate-300">
            <a href="#features">Features</a>
            <a href="#pricing">Pricing</a>
            <a href="#faq">FAQ</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
