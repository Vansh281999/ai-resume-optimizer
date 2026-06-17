import { describe, it, expect } from 'vitest';
import { renderWithProviders } from '../test-utils';
import { screen } from '@testing-library/react';
import { Dashboard } from '../pages/Dashboard';

describe('Dashboard', () => {
  it('renders dashboard container', () => {
    renderWithProviders(<Dashboard />);
    expect(screen.getByText(/Career intelligence/i)).toBeTruthy();
  });

  it('renders job match stat', () => {
    renderWithProviders(<Dashboard />);
    expect(screen.getByText(/Average Job Match/i)).toBeTruthy();
  });

  it('renders navigation sections', () => {
    renderWithProviders(<Dashboard />);
    expect(screen.getByText(/Score trends/i)).toBeTruthy();
  });
});
