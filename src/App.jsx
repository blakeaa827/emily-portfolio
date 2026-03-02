import React, { useEffect, useRef, useState } from 'react';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { FileText, Github, Linkedin, Mail, ExternalLink, ChevronRight, GraduationCap, Syringe, ClipboardList, Briefcase, ChevronDown } from 'lucide-react';
import Copilot from './components/Copilot';

gsap.registerPlugin(ScrollTrigger);

// ---------------------------------------------------------
// DATA CONFIGURATION
// ---------------------------------------------------------

const PROFILE = {
  name: "Emily Maxwell",
  email: "emilyrmaxwel@gmail.com",
  phone: "346.280.3620",
  linkedin: "linkedin.com/in/emily-maxwell-b5b01428a",
  expectedGrad: "May 2029",
  discipline: "Veterinary Medicine",
  heroNoun: "Compassionate Care",
  manifesto: "compassionate diagnostics and client education"
};

const SHUFFLER_CARDS = [
  { id: 1, title: "D.V.M. Candidate", desc: "Undecided Specialty • Michigan State CVM", icon: GraduationCap },
  { id: 2, title: "Clinical Vet Tech", desc: "Advanced Surgical Prep & Triage • Herbst Vet", icon: Syringe },
  { id: 3, title: "B.S. in Animal Science, Minor in Pre-Veterinary Medicine", desc: "Gibbs Ranch \"Living Classroom\" Alum • Huntsville, Texas", icon: ClipboardList }
];

const SKILLS = [
  "SCS 695 ECCM Protocol Integration", "Anesthesia Monitoring & Surgical Prep",
  "Radiography & Diagnostic Imaging", "Gibbs Ranch Large Animal Handling",
  "Emergency Patient Triage", "Phlebotomy & Venipuncture",
  "Complex Pharmaceutical Education", "Level 2b Spanish Communication"
];

const EXPERIENCE = [
  {
    year: "2024 - 2025",
    role: "Veterinary Technician",
    institution: "Herbst Veterinary Hospital • Boerne, TX",
    impact: "Executed advanced surgical preparation, precise anesthetic monitoring, and digital radiography. Functioned as the primary triage responder in high-volume emergency and critical care scenarios, ensuring seamless medical record fidelity."
  },
  {
    year: "2022 - 2024",
    role: "Veterinary Assistant",
    institution: "Bear Branch Animal Hospital • Magnolia, TX",
    impact: "Managed critical translational communication between veterinary specialists and clients. Educated owners on complex pharmaceutical protocols and safely restrained diverse animal cases for venipuncture and diagnostic imaging procedures."
  },
  {
    year: "2017 - 2021",
    role: "General Manager",
    institution: "Native Teachers Idiomas LTDA • Santiago, Chile",
    impact: "Directed a premier immersive linguistic academy utilizing the 'Native Method'. Oversaw hiring, international visa processing, and corporate SENCE-subsidized training operations for high-level business clientele in Santiago."
  }
];

// ---------------------------------------------------------
// COMPONENTS
// ---------------------------------------------------------

const Navbar = () => {
  return (
    <nav className="fixed top-6 left-1/2 -translate-x-1/2 z-50 glass-panel rounded-full px-6 py-3 flex items-center gap-8 text-sm font-medium">
      <div className="font-serif italic text-2xl tracking-tighter pr-6 border-r border-charcoal/10">EM</div>
      <div className="hidden md:flex items-center gap-6">
        <a href="#work" className="hover:text-clay transition-colors hover:underline underline-offset-4">Highlights</a>
        <a href="#philosophy" className="hover:text-clay transition-colors hover:underline underline-offset-4">Philosophy</a>
        <a href="#experience" className="hover:text-clay transition-colors hover:underline underline-offset-4">Experience</a>
      </div>
      <a
        href="#dossier"
        className="magnetic-btn bg-moss text-cream px-5 py-2 rounded-full flex items-center gap-2 hover:bg-moss/90"
      >
        <FileText size={16} />
        <span>View CV</span>
      </a>
    </nav>
  );
};

const Hero = () => {
  const containerRef = useRef(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      const tl = gsap.timeline({ defaults: { ease: "power4.out" } });

      tl.from(".hero-line-1", { y: 50, opacity: 0, duration: 1.2, delay: 0.2 })
        .from(".hero-line-2", { y: 50, opacity: 0, duration: 1.2 }, "-=0.8")
        .from(".hero-desc", { y: 20, opacity: 0, duration: 1 }, "-=0.8");
    }, containerRef);
    return () => ctx.revert();
  }, []);

  return (
    <section ref={containerRef} className="relative h-[100dvh] w-full flex items-end pb-32 px-8 md:px-24">
      {/* Background Image with heavy gradient overlay */}
      <div className="absolute inset-0 z-0">
        <img
          src="https://images.unsplash.com/photo-1548199973-03cce0bbc87b?q=80&w=2680&auto=format&fit=crop"
          alt=""
          className="w-full h-full object-cover opacity-60 mix-blend-multiply"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-charcoal via-charcoal/80 to-transparent"></div>
        <div className="absolute inset-0 bg-gradient-to-r from-charcoal via-charcoal/60 to-transparent"></div>
      </div>

      <div className="relative z-10 max-w-4xl text-left">
        <h1 className="leading-[0.85]">
          <span className="hero-line-1 block font-sans font-bold text-3xl md:text-5xl lg:text-5xl tracking-tight text-cream/90 uppercase mb-2">
            {PROFILE.discipline} driven by
          </span>
          <br />
          <span className="hero-line-2 block font-serif italic text-6xl md:text-8xl lg:text-[10rem] text-cream">
            {PROFILE.heroNoun}
          </span>
        </h1>
        <p className="hero-desc mt-8 font-mono text-cream/70 max-w-xl text-lg md:text-xl space-y-1">
          <span className="block">Michigan State University CVM Class of 2029</span>
          <span className="block">Veterinary Medical Student</span>
          <span className="block">English (Fluent) Spanish (Intermediate)</span>
        </p>

        <div className="hero-desc mt-12 animate-bounce">
          <ChevronDown size={32} className="text-moss" />
        </div>
      </div>
    </section>
  );
};

const ShufflerCard = () => {
  const [activeIdx, setActiveIdx] = useState(0);

  const handleNext = () => {
    setActiveIdx((prev) => (prev + 1) % SHUFFLER_CARDS.length);
  };

  return (
    <div
      onClick={handleNext}
      className="magnetic-btn cursor-pointer relative h-80 w-full glass-panel rounded-[2rem] p-8 flex flex-col justify-between overflow-hidden group"
    >
      <div className="absolute top-0 right-0 p-8 opacity-10 group-hover:opacity-20 transition-opacity">
        <GraduationCap size={120} />
      </div>
      <div>
        <p className="font-mono text-xs text-moss/60 uppercase tracking-widest mb-4">Highlight 01 / Core Roles</p>
        <div className="relative h-24">
          {SHUFFLER_CARDS.map((card, idx) => {
            const isActive = idx === activeIdx;
            const Icon = card.icon;
            return (
              <div
                key={card.id}
                className={`absolute inset-0 transition-all duration-500 ease-spring ${isActive ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4 pointer-events-none'}`}
              >
                <div className="flex items-center gap-4 mb-2">
                  <div className="p-2 bg-moss/10 rounded-full text-moss">
                    <Icon size={24} />
                  </div>
                  <h3 className="font-sans font-bold text-xl md:text-2xl text-moss truncate">{card.title}</h3>
                </div>
                <p className="font-serif italic text-lg md:text-xl text-charcoal/80 ml-14">{card.desc}</p>
              </div>
            );
          })}
        </div>
      </div>
      <div className="flex items-center justify-between mt-auto pt-8 border-t border-charcoal/10">
        <span className="font-mono text-sm text-charcoal/50">Click to cycle roles</span>
        <ChevronRight size={20} className="text-clay group-hover:translate-x-2 transition-transform" />
      </div>
    </div >
  );
};

const TypewriterCard = () => {
  const [text, setText] = useState('');
  const [skillIdx, setSkillIdx] = useState(0);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    if (skillIdx >= SKILLS.length) {
      setSkillIdx(0);
      return;
    }
    const currentSkill = SKILLS[skillIdx];
    if (!currentSkill) return;

    const typeSpeed = isDeleting ? 30 : 80;
    const pauseBeforeDelete = 1500;

    const timeout = setTimeout(() => {
      if (!isDeleting && text === currentSkill) {
        setTimeout(() => setIsDeleting(true), pauseBeforeDelete);
      } else if (isDeleting && text === '') {
        setIsDeleting(false);
        setSkillIdx((prev) => (prev + 1) % SKILLS.length);
      } else {
        const nextText = isDeleting
          ? currentSkill.substring(0, text.length - 1)
          : currentSkill.substring(0, text.length + 1);
        setText(nextText);
      }
    }, typeSpeed);

    return () => clearTimeout(timeout);
  }, [text, isDeleting, skillIdx]);

  return (
    <div className="h-80 w-full backdrop-blur-md border border-white/10 shadow-xl rounded-[2rem] p-8 flex flex-col justify-between bg-moss text-cream">
      <div>
        <p className="font-mono text-xs text-cream/50 uppercase tracking-widest mb-4">Highlight 02 / Clinical Toolkit</p>
        <h3 className="font-sans font-bold text-2xl mb-6">Procedural Competencies</h3>

        <div className="font-mono text-xl md:text-2xl text-cream/90 min-h-[4rem] flex items-start">
          <span>&gt; {text || '\u00A0'}</span>
          <span className="animate-pulse ml-1 inline-block w-3 h-6 bg-clay"></span>
        </div>
      </div>
      <div className="mt-auto pt-8 border-t border-cream/10">
        <p className="font-serif italic text-lg text-cream/70">Hands-on experience in specialized animal care</p>
      </div>
    </div>
  );
};

const TimelineCard = () => {
  return (
    <div className="h-80 w-full glass-panel rounded-[2rem] p-8 flex flex-col justify-between container-snap">
      <div>
        <p className="font-mono text-xs text-moss/60 uppercase tracking-widest mb-6">Highlight 03 / The Trajectory</p>

        <div className="space-y-6 relative before:absolute before:left-3 before:top-2 before:bottom-2 before:w-px before:bg-moss/20">
          <div className="relative pl-8 group">
            <div className="absolute left-0 top-1 w-6 h-6 rounded-full bg-cream border-2 border-clay flex items-center justify-center -translate-x-1.5 z-10">
              <div className="w-2 h-2 rounded-full bg-clay group-hover:scale-150 transition-transform"></div>
            </div>
            <span className="font-mono text-sm font-bold text-clay">May 2029</span>
            <p className="font-serif italic text-lg text-charcoal">Expected Graduation • Undecided Specialty (MSU CVM)</p>
          </div>

          <div className="relative pl-8 group">
            <div className="absolute left-0 top-1 w-6 h-6 rounded-full bg-cream border-2 border-moss/30 flex items-center justify-center -translate-x-1.5 z-10">
              <div className="w-2 h-2 rounded-full bg-moss/30 group-hover:bg-moss transition-colors"></div>
            </div>
            <span className="font-mono text-sm font-bold text-moss">August 2024</span>
            <p className="font-serif italic text-lg text-charcoal">B.S. in Animal Science, Minor in Pre-Veterinary Medicine • Huntsville, Texas</p>
          </div>
        </div>
      </div>
    </div>
  );
};

const Work = () => {
  return (
    <section id="work" className="py-32 px-8 md:px-24 bg-cream">
      <div className="max-w-screen-2xl mx-auto">
        <h2 className="font-sans font-bold text-4xl text-moss mb-12">Interactive Artifacts</h2>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <ShufflerCard />
          <TypewriterCard />
          <TimelineCard />
        </div>
      </div>
    </section>
  );
};

const Philosophy = () => {
  const containerRef = useRef(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      gsap.to(".parallax-bg", {
        yPercent: 30,
        ease: "none",
        scrollTrigger: {
          trigger: containerRef.current,
          start: "top bottom",
          end: "bottom top",
          scrub: true
        }
      });
    }, containerRef);
    return () => ctx.revert();
  }, []);

  return (
    <section id="philosophy" ref={containerRef} className="relative py-32 md:py-48 px-8 md:px-24 overflow-hidden bg-moss text-cream">
      <div className="absolute inset-0 z-0 opacity-20 parallax-bg">
        <img
          src="https://images.unsplash.com/photo-1598287796016-56540c74fb16?q=80&w=2600&auto=format&fit=crop"
          alt=""
          className="w-full h-[150%] object-cover grayscale opacity-80"
        />
      </div>
      <div className="relative z-10 max-w-7xl mx-auto text-center">
        <p className="font-mono text-sm md:text-base text-clay uppercase tracking-widest mb-8">The Manifesto</p>
        <p className="font-sans text-3xl md:text-5xl leading-relaxed text-cream/70 mb-8">
          Standard approaches rely on <br />
          <span className="text-cream font-serif italic text-5xl md:text-7xl">routine transaction</span>
        </p>
        <p className="font-sans text-3xl md:text-5xl leading-tight">
          My work focuses on: <br />
          <span className="font-serif italic text-6xl md:text-8xl lg:text-9xl text-clay block mt-4">
            {PROFILE.manifesto}
          </span>
        </p>
      </div>
    </section>
  );
};

const ExperienceCard = ({ exp, index }) => {
  return (
    <div className={`experience-card w-full h-screen flex items-center justify-center sticky top-0`} style={{ zIndex: index }}>
      <div className="glass-panel w-full max-w-7xl mx-8 md:mx-auto rounded-[3rem] p-12 md:p-24 shadow-2xl border-t border-white/50">
        <div className="flex flex-col md:flex-row gap-12 md:gap-24">
          <div className="md:w-1/3">
            <p className="font-mono text-6xl md:text-8xl font-bold text-moss/20 mb-4">{exp.year.split(' ')[0]}</p>
            <p className="font-mono text-sm text-clay uppercase tracking-widest">{exp.year}</p>
          </div>
          <div className="md:w-2/3">
            <h3 className="font-serif italic text-4xl md:text-5xl text-charcoal mb-4">{exp.role}</h3>
            <p className="font-sans font-semibold text-lg text-moss mb-8">{exp.institution}</p>
            <p className="font-sans text-lg md:text-xl leading-relaxed text-charcoal/80 border-l-2 border-clay pl-6">
              {exp.impact}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

const Experience = () => {
  const containerRef = useRef(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      const cards = gsap.utils.toArray('.experience-card');

      cards.forEach((card, i) => {
        if (i === cards.length - 1) return;

        gsap.to(card, {
          scale: 0.9,
          opacity: 0,
          filter: "blur(20px)",
          ease: "none",
          scrollTrigger: {
            trigger: card,
            start: "top top",
            end: "bottom top",
            scrub: true,
            pin: true,
            pinSpacing: false
          }
        });
      });
    }, containerRef);
    return () => ctx.revert();
  }, []);

  return (
    <section id="experience" ref={containerRef} className="relative bg-cream pb-32">
      <div className="pt-32 px-8 text-center sticky top-0 md:relative z-0">
        <h2 className="font-sans font-bold text-5xl tracking-tight text-moss">Clinical & Operational Record</h2>
      </div>
      {EXPERIENCE.map((exp, idx) => (
        <ExperienceCard key={idx} exp={exp} index={idx + 10} />
      ))}
    </section>
  );
};

const Dossier = () => {
  return (
    <section id="dossier" className="py-32 px-8 md:px-24 bg-charcoal text-cream rounded-t-[3rem] -mt-12 relative z-50">
      <div className="max-w-screen-2xl mx-auto">
        <div className="flex flex-col md:flex-row justify-between items-end border-b border-cream/10 pb-16 mb-16">
          <div>
            <h2 className="font-serif italic text-6xl md:text-8xl text-cream mb-6">The Dossier</h2>
            <div className="flex items-center gap-4">
              <div className="relative flex h-4 w-4">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-clay opacity-75"></span>
                <span className="relative inline-flex rounded-full h-4 w-4 bg-clay"></span>
              </div>
              <p className="font-mono text-sm text-cream/70 uppercase tracking-widest">
                Currently open to Summer Clinical roles working with large animals or in a mixed animal practice
              </p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 lg:gap-16">
          {/* Primary CTA */}
          <a
            href="/Professional%20Resume%20Assignment.pdf"
            download="Emily_Maxwell_CV.pdf"
            target="_blank"
            rel="noopener noreferrer"
            className="magnetic-btn group bg-moss/20 hover:bg-moss/40 border border-moss rounded-[2rem] p-12 transition-colors flex flex-col justify-between h-80"
          >
            <div className="flex justify-between items-start">
              <div className="p-4 bg-moss rounded-full text-cream">
                <FileText size={32} />
              </div>
              <ExternalLink size={24} className="text-cream/50 group-hover:text-cream transition-colors" />
            </div>
            <div>
              <h3 className="font-sans font-bold text-3xl mb-2">Curriculum Vitae</h3>
              <p className="font-serif italic text-xl text-cream/70">Download full pdf</p>
            </div>
          </a>

          {/* Social Links Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-8">
            <a
              href={`https://${PROFILE.linkedin}`}
              target="_blank"
              rel="noopener noreferrer"
              className="magnetic-btn group bg-cream/5 border border-cream/10 hover:border-cream/30 rounded-[2rem] p-8 transition-colors flex flex-col justify-between"
            >
              <div className="flex justify-between items-start">
                <Linkedin size={24} className="text-clay" />
                <ExternalLink size={16} className="text-cream/30 group-hover:text-cream transition-colors" />
              </div>
              <div>
                <h3 className="font-sans font-bold text-xl mb-1">LinkedIn</h3>
                <p className="font-mono text-xs text-cream/50">Professional Network</p>
              </div>
            </a>

            <a
              href={`mailto:${PROFILE.email}`}
              className="magnetic-btn group bg-cream/5 border border-cream/10 hover:border-cream/30 rounded-[2rem] p-8 transition-colors flex flex-col justify-between"
            >
              <div className="flex justify-between items-start">
                <Mail size={24} className="text-clay" />
                <ExternalLink size={16} className="text-cream/30 group-hover:text-cream transition-colors" />
              </div>
              <div>
                <h3 className="font-sans font-bold text-xl mb-1">Email</h3>
                <p className="font-mono text-xs text-cream/50">Direct Contact</p>
              </div>
            </a>
          </div>
        </div>

        <footer className="mt-48 pt-12 border-t border-cream/10 flex flex-col md:flex-row justify-between items-center text-sm font-mono text-cream/40">
          <p>© {new Date().getFullYear()} {PROFILE.name}</p>
          <p
            onClick={() => window.openCopilotLogin?.()}
            className="cursor-pointer hover:text-clay transition-colors"
          >
            Veterinary Medicine Portfolio
          </p>
        </footer>
      </div>
    </section>
  );
};

function App() {
  return (
    <main className="bg-cream selection:bg-clay selection:text-cream">
      <Navbar />
      <Hero />
      <Work />
      <Philosophy />
      <Experience />
      <Dossier />
      <Copilot />
    </main>
  );
}

export default App;