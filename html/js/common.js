const observer = new IntersectionObserver(entries => {
  entries.forEach((e,i) => {
    if(e.isIntersecting){
      e.target.style.transitionDelay = (i * 0.08) + 's';
      e.target.classList.add('visible');
    }
  });
},{threshold:0.1});
document.querySelectorAll('.reveal').forEach(el => observer.observe(el));

// animate bench bars on scroll
const benchObs = new IntersectionObserver(entries => {
  entries.forEach(e => {
    if(e.isIntersecting){
      e.target.querySelectorAll('.bench-bar').forEach(bar => {
        const w = bar.style.width;
        bar.style.width = '0';
        requestAnimationFrame(() => {
          requestAnimationFrame(() => { bar.style.width = w; });
        });
      });
      benchObs.unobserve(e.target);
    }
  });
},{threshold:0.3});
document.querySelectorAll('.tech-panel').forEach(p => benchObs.observe(p));