import React from 'react';
import { fireEvent, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import AiAdvisorManagement from './AiAdvisorManagement';
import { getAiAdvisor, getPonds } from '../../test/mocks/api';
import { aiAdvice, ponds } from '../../test/mocks/data';
import { renderWithProviders } from '../../test/utils/testUtils';

vi.mock('../../lib/api', () => import('../../test/mocks/api'));

describe('AiAdvisorManagement', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getPonds.mockResolvedValue(ponds);
    getAiAdvisor.mockResolvedValue(aiAdvice);
  });

  it('loads ponds and displays advice for the first pond', async () => {
    renderWithProviders(<AiAdvisorManagement />);

    expect(await screen.findByText('Improve water quality before the next feeding.'))
      .toBeInTheDocument();

    expect(getPonds).toHaveBeenCalledTimes(1);
    expect(getAiAdvisor).toHaveBeenCalledWith('1');
    expect(screen.getByText('Check dissolved oxygen')).toBeInTheDocument();
    expect(screen.getByText('Low oxygen levels')).toBeInTheDocument();
    expect(screen.getByText('Test the pond water today')).toBeInTheDocument();
  });

  it('loads advice for a different pond when the selection changes', async () => {
    renderWithProviders(<AiAdvisorManagement />);
    await screen.findByText('Improve water quality before the next feeding.');

    const select = screen.getByRole('combobox', { name: 'Pond' });
    fireEvent.change(select, { target: { value: '2' } });

    await waitFor(() => expect(getAiAdvisor).toHaveBeenLastCalledWith('2'));
  });

  it('shows the empty state when the user has no ponds', async () => {
    getPonds.mockResolvedValueOnce([]);
    renderWithProviders(<AiAdvisorManagement />);

    expect(await screen.findByText('Add a pond before generating AI recommendations.'))
      .toBeInTheDocument();
    expect(getAiAdvisor).not.toHaveBeenCalled();
  });

  it('shows an error when advice cannot be loaded', async () => {
    getAiAdvisor.mockRejectedValueOnce(new Error('Advisor service unavailable'));
    renderWithProviders(<AiAdvisorManagement />);

    expect(await screen.findByText('Advisor service unavailable')).toBeInTheDocument();
    expect(screen.queryByText('Improve water quality before the next feeding.'))
      .not.toBeInTheDocument();
  });
});
