document.querySelectorAll('input[type="password"], input[data-password-toggle]').forEach((input) => {
  const parent = input.parentElement;
  if (!parent) return;
  const initiallyVisible = input.type === 'text';

  const control = document.createElement('div');
  control.className = 'password-control';
  parent.insertBefore(control, input);
  control.append(input);

  const toggle = document.createElement('button');
  toggle.className = 'password-toggle';
  toggle.type = 'button';
  toggle.textContent = initiallyVisible ? 'Hide' : 'Show';
  toggle.setAttribute('aria-label', `${initiallyVisible ? 'Hide' : 'Show'} password`);
  toggle.setAttribute('aria-pressed', String(initiallyVisible));
  toggle.addEventListener('click', () => {
    const showPassword = input.type === 'password';
    input.type = showPassword ? 'text' : 'password';
    toggle.textContent = showPassword ? 'Hide' : 'Show';
    toggle.setAttribute('aria-label', `${showPassword ? 'Hide' : 'Show'} password`);
    toggle.setAttribute('aria-pressed', String(showPassword));
  });
  control.append(toggle);
});