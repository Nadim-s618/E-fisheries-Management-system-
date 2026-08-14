import React from 'react';
import { fireEvent, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import FeedingManagement from '../components/feeding/FeedingManagement';
import { acceptFeedingRecommendation, completeFeedingSession, getFeedingDashboard, getPonds } from '../test/mocks/feedingApi';
import { activePlan, feedingHistory, feedingPonds, feedingRecommendation } from '../test/mocks/feedingData';
import { renderWithProviders } from '../test/utils/testUtils';

vi.mock('../lib/api', () => import('../test/mocks/feedingApi'));

const draft = { recommendation: feedingRecommendation, active_plan: null, pending_sessions: [], history: feedingHistory };
const tracked = { recommendation: { ...feedingRecommendation, status: 'accepted' }, active_plan: activePlan, pending_sessions: [], history: feedingHistory };

describe('feeding integration flow', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getPonds.mockResolvedValue(feedingPonds);
    getFeedingDashboard.mockResolvedValue(draft);
    acceptFeedingRecommendation.mockResolvedValue({});
    completeFeedingSession.mockResolvedValue({});
  });

  it('accepts a recommendation and opens the active feeding tracker', async () => {
    getFeedingDashboard.mockResolvedValueOnce(draft).mockResolvedValueOnce(tracked);
    renderWithProviders(<FeedingManagement />);
    await screen.findByText("Today's Feeding Recommendation");
    fireEvent.click(screen.getByRole('button', { name: 'Accept' }));

    await waitFor(() => expect(acceptFeedingRecommendation).toHaveBeenCalledWith(21));
    expect(await screen.findByText('Active Feed')).toBeInTheDocument();
  });

  it('does not call feeding APIs when there are no ponds', async () => {
    getPonds.mockResolvedValueOnce([]);
    renderWithProviders(<FeedingManagement />);
    expect(await screen.findByText('Add a pond before generating feeding recommendations.')).toBeInTheDocument();
    expect(getFeedingDashboard).not.toHaveBeenCalled();
  });
});
