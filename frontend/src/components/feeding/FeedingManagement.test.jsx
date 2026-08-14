import React from 'react';
import { fireEvent, screen, waitFor, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import FeedingManagement from './FeedingManagement';
import {
  acceptFeedingRecommendation,
  completeFeedingSession,
  editFeedingRecommendation,
  getFeedingDashboard,
  getPonds,
} from '../../test/mocks/feedingApi';
import {
  activePlan,
  feedingHistory,
  feedingPonds,
  feedingRecommendation,
} from '../../test/mocks/feedingData';
import { renderWithProviders } from '../../test/utils/testUtils';

vi.mock('../../lib/api', () => import('../../test/mocks/feedingApi'));

const draftDashboard = {
  recommendation: feedingRecommendation,
  active_plan: null,
  pending_sessions: [],
  history: feedingHistory,
};

const trackedDashboard = {
  recommendation: { ...feedingRecommendation, status: 'accepted' },
  active_plan: activePlan,
  pending_sessions: [],
  history: feedingHistory,
};

describe('FeedingManagement', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getPonds.mockResolvedValue(feedingPonds);
    getFeedingDashboard.mockResolvedValue(draftDashboard);
    acceptFeedingRecommendation.mockResolvedValue({});
    editFeedingRecommendation.mockResolvedValue({});
    completeFeedingSession.mockResolvedValue({});
  });

  it('loads and displays the recommendation for the first pond', async () => {
    renderWithProviders(<FeedingManagement />);

    expect(await screen.findByText("Today's Feeding Recommendation")).toBeInTheDocument();
    const recommendation = screen.getByRole('region', { name: "Today's feeding recommendation" });
    expect(within(recommendation).getByText('North Pond')).toBeInTheDocument();
    expect(screen.getByText('12.5 kg')).toBeInTheDocument();
    expect(screen.getByText('Floating Feed 32%')).toBeInTheDocument();
    expect(screen.getByText('Feed consistently to support healthy growth.'))
      .toBeInTheDocument();
    expect(getFeedingDashboard).toHaveBeenCalledWith('1');
  });

  it('reloads feeding data when the pond changes', async () => {
    renderWithProviders(<FeedingManagement />);
    await screen.findByText("Today's Feeding Recommendation");

    fireEvent.change(screen.getByRole('combobox', { name: 'Pond' }), {
      target: { value: '2' },
    });

    await waitFor(() => expect(getFeedingDashboard).toHaveBeenLastCalledWith('2'));
  });

  it('shows the empty state when there are no ponds', async () => {
    getPonds.mockResolvedValueOnce([]);
    renderWithProviders(<FeedingManagement />);

    expect(await screen.findByText('Add a pond before generating feeding recommendations.'))
      .toBeInTheDocument();
    expect(getFeedingDashboard).not.toHaveBeenCalled();
  });

  it('accepts a draft recommendation and opens the tracker', async () => {
    getFeedingDashboard
      .mockResolvedValueOnce(draftDashboard)
      .mockResolvedValueOnce(trackedDashboard);
    const onNotificationChange = vi.fn();

    renderWithProviders(<FeedingManagement onNotificationChange={onNotificationChange} />);
    await screen.findByText("Today's Feeding Recommendation");

    fireEvent.click(screen.getByRole('button', { name: 'Accept' }));

    await screen.findByText('Active Feed');
    expect(acceptFeedingRecommendation).toHaveBeenCalledWith(21);
    expect(onNotificationChange).toHaveBeenCalledTimes(1);
    expect(screen.getAllByText('Completed').length).toBeGreaterThan(0);
    expect(screen.getByText('Pending')).toBeInTheDocument();
  });

  it('completes a pending feeding session with the entered amount', async () => {
    getFeedingDashboard
      .mockResolvedValueOnce(trackedDashboard)
      .mockResolvedValueOnce(trackedDashboard);
    const onNotificationChange = vi.fn();

    renderWithProviders(<FeedingManagement onNotificationChange={onNotificationChange} />);
    await screen.findByText("Today's Feeding Recommendation");
    fireEvent.click(screen.getByRole('button', { name: 'Tracker' }));

    const amount = screen.getByRole('spinbutton', { name: 'Actual feed for meal 1' });
    fireEvent.change(amount, { target: { value: '6' } });
    fireEvent.click(screen.getByRole('button', { name: 'Complete' }));

    await waitFor(() => expect(completeFeedingSession).toHaveBeenCalledWith(101, {
      actual_feed_kg: 6,
    }));
    expect(onNotificationChange).toHaveBeenCalledTimes(1);
  });

  it('renders feeding history in the History tab', async () => {
    renderWithProviders(<FeedingManagement />);
    await screen.findByText("Today's Feeding Recommendation");
    fireEvent.click(screen.getByRole('button', { name: 'History' }));

    expect(screen.getByRole('columnheader', { name: 'Date' })).toBeInTheDocument();
    expect(screen.getByText('Aug 13')).toBeInTheDocument();
    expect(screen.getByText('Completed')).toBeInTheDocument();
    expect(screen.getByText('TK 1,485.00')).toBeInTheDocument();
  });
});
