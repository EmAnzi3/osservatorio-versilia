(() => {
  'use strict';

  const MOBILE_QUERY = '(max-width: 700px)';
  const HEADING_SELECTOR = '.metric-group-heading, .indicator-group-heading';
  let counter = 0;
  let scheduled = false;

  function setOpen(group, open) {
    const content = group.querySelector(':scope > .metric-group-buttons, :scope > .indicator-card-grid');
    const heading = group.querySelector(':scope > .metric-group-heading, :scope > .indicator-group-heading');
    if (!content || !heading) return;
    group.classList.toggle('is-open', open);
    content.hidden = !open;
    heading.setAttribute('aria-expanded', open ? 'true' : 'false');
  }

  function directGroups(container, groupSelector) {
    return [...container.querySelectorAll(`:scope > ${groupSelector}`)];
  }

  function decorateGroup(group) {
    const heading = group.querySelector(':scope > .metric-group-heading, :scope > .indicator-group-heading');
    const content = group.querySelector(':scope > .metric-group-buttons, :scope > .indicator-card-grid');
    if (!heading || !content) return;

    const count = content.querySelectorAll('button').length;
    const id = content.id || `ux-section-${++counter}`;
    content.id = id;
    heading.classList.add('ux-section-toggle');
    heading.setAttribute('role', 'button');
    heading.setAttribute('tabindex', '0');
    heading.setAttribute('aria-controls', id);

    let tools = heading.querySelector(':scope > .ux-section-tools');
    if (!tools) {
      heading.insertAdjacentHTML(
        'beforeend',
        '<span class="ux-section-tools"><span></span><span class="ux-section-chevron" aria-hidden="true">⌄</span></span>'
      );
      tools = heading.querySelector(':scope > .ux-section-tools');
    }
    const countLabel = tools?.querySelector(':scope > span:first-child');
    const label = `${count} ${count === 1 ? 'indicatore' : 'indicatori'}`;
    if (countLabel && countLabel.textContent !== label) countLabel.textContent = label;

    group.dataset.uxAccordion = 'true';
    heading.dataset.uxAccordionHeading = 'true';
  }

  function toggleGroup(container, groupSelector, group) {
    const groups = directGroups(container, groupSelector);
    const opening = !group.classList.contains('is-open');
    if (opening && window.matchMedia(MOBILE_QUERY).matches) {
      groups.forEach(other => { if (other !== group) setOpen(other, false); });
    }
    setOpen(group, opening);
  }

  function installDelegatedHandlers(container, groupSelector) {
    if (container.dataset.uxAccordionDelegated === 'true') return;

    const resolve = target => {
      const heading = target?.closest?.(HEADING_SELECTOR);
      if (!heading || !container.contains(heading)) return null;
      const group = heading.closest(groupSelector);
      if (!group || group.parentElement !== container) return null;
      return { heading, group };
    };

    container.addEventListener('click', event => {
      const match = resolve(event.target);
      if (!match) return;
      toggleGroup(container, groupSelector, match.group);
    });

    container.addEventListener('keydown', event => {
      if (event.key !== 'Enter' && event.key !== ' ') return;
      const match = resolve(event.target);
      if (!match || event.target !== match.heading) return;
      event.preventDefault();
      toggleGroup(container, groupSelector, match.group);
    });

    container.dataset.uxAccordionDelegated = 'true';
  }

  function installVisibleTabKeyboard(container) {
    if (!container.matches('[role="tablist"]') || container.dataset.uxVisibleTabs === 'true') return;
    container.addEventListener('keydown', event => {
      if (!['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Home', 'End'].includes(event.key)) return;
      const target = event.target.closest?.('[role="tab"]');
      if (!target) return;
      const visible = [...container.querySelectorAll('[role="tab"]')].filter(tab => !tab.closest('[hidden]'));
      const current = visible.indexOf(target);
      if (current < 0 || !visible.length) return;
      event.preventDefault();
      event.stopImmediatePropagation();
      let next = current;
      if (event.key === 'ArrowRight' || event.key === 'ArrowDown') next = (current + 1) % visible.length;
      else if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') next = (current - 1 + visible.length) % visible.length;
      else if (event.key === 'Home') next = 0;
      else if (event.key === 'End') next = visible.length - 1;
      visible[next]?.focus();
      visible[next]?.click();
    }, true);
    container.dataset.uxVisibleTabs = 'true';
  }

  function prepare(container, groupSelector) {
    if (!container) return;
    const groups = directGroups(container, groupSelector);
    if (!groups.length) return;

    groups.forEach(decorateGroup);
    installDelegatedHandlers(container, groupSelector);
    installVisibleTabKeyboard(container);

    const activeGroup = groups.find(group => group.querySelector('.active')) || groups[0];
    const total = groups.reduce((sum, group) => sum + group.querySelectorAll('button').length, 0);
    const compact = total > 6;
    const mobile = window.matchMedia(MOBILE_QUERY).matches;

    if (container.dataset.uxAccordionReady !== 'true') {
      groups.forEach(group => setOpen(group, mobile || compact ? group === activeGroup : true));
      container.dataset.uxAccordionReady = 'true';
    } else if (activeGroup && !activeGroup.classList.contains('is-open')) {
      if (mobile) groups.forEach(group => setOpen(group, group === activeGroup));
      else setOpen(activeGroup, true);
    }
  }

  function enhance() {
    document.querySelectorAll('.metric-catalog').forEach(container => prepare(container, '.metric-group'));
    document.querySelectorAll('.indicator-groups').forEach(container => prepare(container, '.indicator-group'));
  }

  function schedule() {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(() => {
      scheduled = false;
      enhance();
    });
  }

  new MutationObserver(schedule).observe(document.documentElement, { childList: true, subtree: true });
  window.matchMedia(MOBILE_QUERY).addEventListener?.('change', schedule);
  schedule();
})();
