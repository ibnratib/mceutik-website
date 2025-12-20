(function() {
  "use strict";

  /**
   * Apply shadow on scroll
   */
  function toggleScrolled() {
    const header = document.querySelector('header');
    if (!header) return;
    
    if (window.scrollY > 100) {
      header.classList.remove('bg-white/90');
      header.classList.add('bg-white', 'shadow-md');
    } else {
      header.classList.remove('bg-white', 'shadow-md');
      header.classList.add('bg-white/90');
    }
  }

  document.addEventListener('scroll', toggleScrolled);
  window.addEventListener('load', toggleScrolled);

  /**
   * Mobile nav toggle
   */
  const mobileNavToggleBtn = document.querySelector('.bi-list');
  const nav = document.querySelector('nav');

  function mobileNavToggle() {
    if (!nav || !mobileNavToggleBtn) return;
    
    // Toggle navigation visibility
    nav.classList.toggle('hidden');
    nav.classList.toggle('flex');
    nav.classList.toggle('flex-col');
    nav.classList.toggle('absolute');
    nav.classList.toggle('top-full');
    nav.classList.toggle('left-0');
    nav.classList.toggle('w-full');
    nav.classList.toggle('bg-white');
    nav.classList.toggle('shadow-lg');
    nav.classList.toggle('p-6');
    
    // Toggle icon
    mobileNavToggleBtn.classList.toggle('bi-list');
    mobileNavToggleBtn.classList.toggle('bi-x');
  }

  if (mobileNavToggleBtn) {
    mobileNavToggleBtn.addEventListener('click', mobileNavToggle);
  }

  /**
   * Hide mobile nav on link click
   */
  document.querySelectorAll('nav a').forEach(link => {
    link.addEventListener('click', () => {
      if (nav && !nav.classList.contains('hidden') && window.innerWidth < 768) {
        mobileNavToggle();
      }
    });
  });

  /**
   * Scroll top button (si vous en ajoutez un)
   */
  const scrollTop = document.querySelector('.scroll-top');

  function toggleScrollTop() {
    if (scrollTop) {
      window.scrollY > 100 ? scrollTop.classList.add('active') : scrollTop.classList.remove('active');
    }
  }

  if (scrollTop) {
    scrollTop.addEventListener('click', (e) => {
      e.preventDefault();
      window.scrollTo({
        top: 0,
        behavior: 'smooth'
      });
    });

    window.addEventListener('load', toggleScrollTop);
    document.addEventListener('scroll', toggleScrollTop);
  }

  /**
   * Correct scrolling position upon page load for URLs containing hash links
   */
  window.addEventListener('load', function(e) {
    if (window.location.hash) {
      const section = document.querySelector(window.location.hash);
      if (section) {
        setTimeout(() => {
          const headerHeight = document.querySelector('header').offsetHeight;
          window.scrollTo({
            top: section.offsetTop - headerHeight - 20,
            behavior: 'smooth'
          });
        }, 100);
      }
    }
  });

  /**
   * Navmenu Scrollspy - Active link highlighting
   */
  const navLinks = document.querySelectorAll('nav a');

  function navScrollspy() {
    navLinks.forEach(link => {
      if (!link.hash) return;
      
      const section = document.querySelector(link.hash);
      if (!section) return;
      
      const headerHeight = document.querySelector('header').offsetHeight;
      const position = window.scrollY + headerHeight + 50;
      
      if (position >= section.offsetTop && position <= (section.offsetTop + section.offsetHeight)) {
        navLinks.forEach(l => l.classList.remove('text-primary', 'font-semibold'));
        link.classList.add('text-primary', 'font-semibold');
      } else {
        link.classList.remove('text-primary', 'font-semibold');
      }
    });
  }

  window.addEventListener('load', navScrollspy);
  document.addEventListener('scroll', navScrollspy);

  /**
   * Smooth scroll for anchor links
   */
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      const href = this.getAttribute('href');
      if (href === '#') return;
      
      const section = document.querySelector(href);
      if (section) {
        e.preventDefault();
        const headerHeight = document.querySelector('header').offsetHeight;
        window.scrollTo({
          top: section.offsetTop - headerHeight - 20,
          behavior: 'smooth'
        });
      }
    });
  });

})();