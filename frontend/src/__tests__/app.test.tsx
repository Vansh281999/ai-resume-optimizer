import { describe, it, expect } from 'vitest';
import { renderWithProviders } from '../test-utils';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Landing } from '../pages/Landing';
import { Login } from '../pages/Login';
import { Signup } from '../pages/Signup';

describe('Landing', () => {
  it('renders hero heading', () => {
    renderWithProviders(<Landing />);
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(/Optimize your resume/i);
  });

  it('renders signup link', () => {
    renderWithProviders(<Landing />);
    const link = screen.getByRole('link', { name: /get started/i });
    expect(link).toBeTruthy();
    expect(link.getAttribute('href')).toBe('/signup');
  });

  it('renders pricing cards by current names', () => {
    renderWithProviders(<Landing />);
    expect(screen.getByText('Starter')).toBeTruthy();
    expect(screen.getByText('Professional')).toBeTruthy();
    expect(screen.getByText('Team')).toBeTruthy();
  });
});

describe('Login', () => {
  it('renders inputs', () => {
    renderWithProviders(<Login />, { route: '/login' });
    expect(screen.getByLabelText(/email address/i)).toBeTruthy();
    const passwordInputs = screen.getAllByLabelText(/password/i);
    expect(passwordInputs.length).toBeGreaterThan(0);
  });

  it('shows validation error on empty submit', async () => {
    const user = userEvent.setup();
    renderWithProviders(<Login />, { route: '/login' });
    await user.click(screen.getByRole('button', { name: /sign in/i }));
    expect(screen.getByText(/email and password are required/i)).toBeTruthy();
  });
});

describe('Signup', () => {
  it('renders fields', () => {
    renderWithProviders(<Signup />, { route: '/signup' });
    expect(screen.getByLabelText(/full name/i)).toBeTruthy();
    expect(screen.getByLabelText(/email address/i)).toBeTruthy();
    const passwordInputs = screen.getAllByLabelText(/password/i);
    expect(passwordInputs.length).toBeGreaterThan(0);
  });

  it('shows validation error on empty submit', async () => {
    const user = userEvent.setup();
    renderWithProviders(<Signup />, { route: '/signup' });
    await user.click(screen.getByRole('button', { name: /create account/i }));
    expect(screen.getByText(/all fields are required/i)).toBeTruthy();
  });
});
