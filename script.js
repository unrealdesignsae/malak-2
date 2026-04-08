/* ==========================================================================
   UNREAL STUDIO — Interactions & Animations
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {

    // ---------- Hide Spline Watermark ----------
    function hideSplineWatermark() {
        const viewer = document.querySelector('spline-viewer');
        if (!viewer || !viewer.shadowRoot) return false;
        const logo = viewer.shadowRoot.querySelector('#logo');
        if (logo) {
            logo.style.display = 'none';
            logo.style.visibility = 'hidden';
            logo.style.opacity = '0';
            logo.style.pointerEvents = 'none';
            return true;
        }
        return false;
    }
    // Try immediately, then retry every 500ms until found (Spline loads async)
    const watermarkInterval = setInterval(() => {
        if (hideSplineWatermark()) clearInterval(watermarkInterval);
    }, 500);
    // Stop trying after 15 seconds
    setTimeout(() => clearInterval(watermarkInterval), 15000);


    // ---------- Loader ----------
    const loader = document.getElementById('loader');
    window.addEventListener('load', () => {
        setTimeout(() => {
            loader.classList.add('loaded');
            document.body.style.overflow = '';
            initAnimations();
        }, 2000);
    });

    // Fallback: Remove loader after 4 seconds max
    setTimeout(() => {
        if (!loader.classList.contains('loaded')) {
            loader.classList.add('loaded');
            document.body.style.overflow = '';
            initAnimations();
        }
    }, 4000);

    // ---------- Custom Cursor ----------
    const cursor = document.getElementById('cursor');
    const follower = document.getElementById('cursor-follower');
    let mouseX = 0, mouseY = 0;
    let followerX = 0, followerY = 0;

    if (window.matchMedia('(pointer: fine)').matches) {
        document.addEventListener('mousemove', (e) => {
            mouseX = e.clientX;
            mouseY = e.clientY;
            cursor.style.transform = `translate(${mouseX - 4}px, ${mouseY - 4}px)`;
        });

        function animateFollower() {
            followerX += (mouseX - followerX) * 0.12;
            followerY += (mouseY - followerY) * 0.12;
            follower.style.transform = `translate(${followerX - 18}px, ${followerY - 18}px)`;
            requestAnimationFrame(animateFollower);
        }
        animateFollower();

        // Hover effects on interactive elements
        const hoverTargets = document.querySelectorAll('a, button, .service-card, .work-card, .testimonial-card');
        hoverTargets.forEach(el => {
            el.addEventListener('mouseenter', () => follower.classList.add('hover'));
            el.addEventListener('mouseleave', () => follower.classList.remove('hover'));
        });
    }

    // ---------- Navbar Scroll ----------
    const navbar = document.getElementById('navbar');
    let lastScroll = 0;

    window.addEventListener('scroll', () => {
        const scrollY = window.scrollY;
        if (scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
        lastScroll = scrollY;
    }, { passive: true });

    // ---------- Mobile Menu ----------
    const menuToggle = document.getElementById('menuToggle');
    const navLinks = document.getElementById('navLinks');

    menuToggle.addEventListener('click', () => {
        const isOpen = navLinks.classList.toggle('open');
        menuToggle.classList.toggle('active');
        menuToggle.setAttribute('aria-expanded', isOpen);
        document.body.style.overflow = isOpen ? 'hidden' : '';
    });

    // Close menu on link click
    navLinks.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', () => {
            navLinks.classList.remove('open');
            menuToggle.classList.remove('active');
            menuToggle.setAttribute('aria-expanded', 'false');
            document.body.style.overflow = '';
        });
    });

    // ---------- Smooth Scroll ----------
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', (e) => {
            e.preventDefault();
            const target = document.querySelector(anchor.getAttribute('href'));
            if (target) {
                const offset = navbar.offsetHeight + 20;
                const targetPosition = target.getBoundingClientRect().top + window.scrollY - offset;
                window.scrollTo({ top: targetPosition, behavior: 'smooth' });
            }
        });
    });

    // ---------- Typewriter Effect ----------
    const typedTextEl = document.getElementById('typedText');
    const phrases = [
        'agentic AI systems.',
        'intelligent design.',
        'autonomous marketing engines.',
        'AI-powered experiences.',
        'the future of business.'
    ];
    let phraseIndex = 0;
    let charIndex = 0;
    let isDeleting = false;
    let typingSpeed = 80;

    function typeWriter() {
        const currentPhrase = phrases[phraseIndex];

        if (isDeleting) {
            typedTextEl.textContent = currentPhrase.substring(0, charIndex - 1);
            charIndex--;
            typingSpeed = 40;
        } else {
            typedTextEl.textContent = currentPhrase.substring(0, charIndex + 1);
            charIndex++;
            typingSpeed = 80;
        }

        if (!isDeleting && charIndex === currentPhrase.length) {
            isDeleting = true;
            typingSpeed = 2000; // Pause at end
        } else if (isDeleting && charIndex === 0) {
            isDeleting = false;
            phraseIndex = (phraseIndex + 1) % phrases.length;
            typingSpeed = 500; // Pause before next phrase
        }

        setTimeout(typeWriter, typingSpeed);
    }

    // ---------- Counter Animation ----------
    function animateCounters() {
        const counters = document.querySelectorAll('.stat-number[data-target]');
        counters.forEach(counter => {
            if (counter.dataset.animated) return;

            const target = parseInt(counter.dataset.target);
            const duration = 2000;
            const startTime = performance.now();

            function updateCounter(currentTime) {
                const elapsed = currentTime - startTime;
                const progress = Math.min(elapsed / duration, 1);
                // Ease out cubic
                const eased = 1 - Math.pow(1 - progress, 3);
                const current = Math.floor(eased * target);
                counter.textContent = current;

                if (progress < 1) {
                    requestAnimationFrame(updateCounter);
                } else {
                    counter.textContent = target;
                    counter.dataset.animated = 'true';
                }
            }

            requestAnimationFrame(updateCounter);
        });
    }

    // ---------- Scroll Reveal Animations ----------
    function initAnimations() {
        const revealElements = document.querySelectorAll('.reveal-up, .reveal-left, .reveal-right');

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const delay = entry.target.dataset.delay || 0;
                    setTimeout(() => {
                        entry.target.classList.add('visible');
                    }, parseInt(delay));

                    // Trigger counters when stats section is visible
                    if (entry.target.querySelector('.stat-number[data-target]') ||
                        entry.target.classList.contains('hero-stats') ||
                        entry.target.closest('.about-stats')) {
                        setTimeout(animateCounters, parseInt(delay) + 300);
                    }

                    observer.unobserve(entry.target);
                }
            });
        }, {
            threshold: 0.15,
            rootMargin: '0px 0px -40px 0px'
        });

        revealElements.forEach(el => observer.observe(el));

        // Start typewriter
        setTimeout(typeWriter, 1000);
    }

    // ---------- Contact Form ----------
    const contactForm = document.getElementById('contactForm');
    const formSuccess = document.getElementById('formSuccess');
    const submitBtn = document.getElementById('submitBtn');

    contactForm.addEventListener('submit', (e) => {
        e.preventDefault();

        // Basic validation
        const name = document.getElementById('name').value.trim();
        const email = document.getElementById('email').value.trim();
        const service = document.getElementById('service').value;
        const message = document.getElementById('message').value.trim();

        if (!name || !email || !service || !message) {
            shakeButton(submitBtn);
            return;
        }

        if (!isValidEmail(email)) {
            shakeButton(submitBtn);
            return;
        }

        // Hide any previous success/error messages
        formSuccess.hidden = true;
        formSuccess.classList.remove('form-error');

        // Submit via FormSubmit API (sends real email to hello@unreal.ae)
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span>Sending...</span>';

        const formData = new FormData(contactForm);

        fetch(contactForm.action, {
            method: 'POST',
            body: formData,
            headers: { 'Accept': 'application/json' }
        })
        .then(response => {
            if (response.ok) {
                formSuccess.hidden = false;
                formSuccess.innerHTML = `
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
                    <p>Message sent successfully! We'll be in touch within 24 hours.</p>
                `;
                contactForm.reset();
            } else {
                throw new Error('Failed to send');
            }
        })
        .catch(() => {
            // Show error + fallback mailto link
            formSuccess.hidden = false;
            formSuccess.classList.add('form-error');
            formSuccess.innerHTML = `
                <p>Could not send automatically. <a href="mailto:hello@unreal.ae?subject=${encodeURIComponent('New Project Inquiry — ' + service)}&body=${encodeURIComponent('Name: ' + name + '\nEmail: ' + email + '\nService: ' + service + '\n\nMessage:\n' + message)}" style="color:var(--accent);text-decoration:underline;">Click here to email us directly.</a></p>
            `;
        })
        .finally(() => {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<span>Send Message</span><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/></svg>';
        });
    });

    function isValidEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }

    function shakeButton(btn) {
        btn.style.animation = 'shake 0.5s ease';
        setTimeout(() => {
            btn.style.animation = '';
        }, 500);
    }

    // Add shake keyframes dynamically
    const styleSheet = document.createElement('style');
    styleSheet.textContent = `
        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            25% { transform: translateX(-8px); }
            50% { transform: translateX(8px); }
            75% { transform: translateX(-4px); }
        }
    `;
    document.head.appendChild(styleSheet);

    // ---------- Parallax Orbs & Mouse Spotlight ----------
    const heroSection = document.querySelector('.hero');
    const orbs = document.querySelectorAll('.orb');
    const mouseSpotlight = document.getElementById('mouseSpotlight');

    if (window.matchMedia('(pointer: fine)').matches && heroSection) {
        heroSection.addEventListener('mousemove', (e) => {
            const rect = heroSection.getBoundingClientRect();
            const x = (e.clientX - rect.left) / rect.width - 0.5;
            const y = (e.clientY - rect.top) / rect.height - 0.5;

            orbs.forEach((orb, i) => {
                const speed = (i + 1) * 15;
                orb.style.transform = `translate(${x * speed}px, ${y * speed}px)`;
            });

            // Move spotlight to cursor position
            if (mouseSpotlight) {
                mouseSpotlight.style.left = `${e.clientX - rect.left}px`;
                mouseSpotlight.style.top = `${e.clientY - rect.top}px`;
            }
        });
    }

    // ---------- Active Nav Link on Scroll ----------
    const sections = document.querySelectorAll('section[id]');
    const navItems = document.querySelectorAll('.nav-links a[href^="#"]');

    window.addEventListener('scroll', () => {
        let current = '';
        sections.forEach(section => {
            const sectionTop = section.offsetTop - 200;
            if (window.scrollY >= sectionTop) {
                current = section.getAttribute('id');
            }
        });

        navItems.forEach(item => {
            item.classList.remove('active');
            if (item.getAttribute('href') === `#${current}`) {
                item.classList.add('active');
            }
        });
    }, { passive: true });

});
