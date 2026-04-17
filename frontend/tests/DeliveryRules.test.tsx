/**
 * Tests for DeliveryRules component.
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { DeliveryRules } from '../src/components/DeliveryRules';

describe('DeliveryRules', () => {
  const mockRules = [
    {
      id: 'rule-1',
      triggerType: 'high_cost_query',
      channelType: 'email',
      enabled: true,
      alertLevels: ['critical', 'warning'],
    },
  ];

  const mockChannels = ['email', 'slack', 'pagerduty'];
  const mockTriggerTypes = ['high_cost_query', 'slow_query', 'error_spike'];

  test('should render delivery rules', () => {
    render(
      <DeliveryRules
        rules={mockRules}
        channels={mockChannels}
        triggerTypes={mockTriggerTypes}
      />
    );

    expect(screen.getByText('Delivery Rules')).toBeInTheDocument();
    expect(screen.getByText('high_cost_query → email')).toBeInTheDocument();
  });

  test('should show rule details', () => {
    render(
      <DeliveryRules
        rules={mockRules}
        channels={mockChannels}
        triggerTypes={mockTriggerTypes}
      />
    );

    expect(screen.getByText('Critical')).toBeInTheDocument();
    expect(screen.getByText('Warning')).toBeInTheDocument();
  });

  test('should toggle rule enabled state', () => {
    const onUpdateRule = jest.fn();
    const { container } = render(
      <DeliveryRules
        rules={mockRules}
        channels={mockChannels}
        triggerTypes={mockTriggerTypes}
        onUpdateRule={onUpdateRule}
      />
    );

    const checkbox = container.querySelector('input[type="checkbox"]') as HTMLInputElement;
    fireEvent.click(checkbox);

    expect(onUpdateRule).toHaveBeenCalled();
  });

  test('should call onRemoveRule when removing rule', () => {
    const onRemoveRule = jest.fn();
    render(
      <DeliveryRules
        rules={mockRules}
        channels={mockChannels}
        triggerTypes={mockTriggerTypes}
        onRemoveRule={onRemoveRule}
      />
    );

    const removeButton = screen.getByText('Remove');
    fireEvent.click(removeButton);

    expect(onRemoveRule).toHaveBeenCalledWith('rule-1');
  });

  test('should add new rule', () => {
    const onAddRule = jest.fn();
    const { container } = render(
      <DeliveryRules
        rules={mockRules}
        channels={mockChannels}
        triggerTypes={mockTriggerTypes}
        onAddRule={onAddRule}
      />
    );

    const addButton = screen.getByText('+ Add Rule');
    fireEvent.click(addButton);

    const selects = container.querySelectorAll('select');
    fireEvent.change(selects[0], { target: { value: 'high_cost_query' } });
    fireEvent.change(selects[1], { target: { value: 'email' } });

    const submitButton = screen.getByText('Add Rule');
    fireEvent.click(submitButton);

    expect(onAddRule).toHaveBeenCalled();
  });

  test('should show alert level selection', () => {
    const { container } = render(
      <DeliveryRules
        rules={mockRules}
        channels={mockChannels}
        triggerTypes={mockTriggerTypes}
      />
    );

    const criticalButton = screen.getByText('Critical');
    expect(criticalButton).toBeInTheDocument();
  });

  test('should handle empty rules list', () => {
    render(
      <DeliveryRules
        rules={[]}
        channels={mockChannels}
        triggerTypes={mockTriggerTypes}
      />
    );

    expect(screen.getByText('+ Add Rule')).toBeInTheDocument();
  });

  test('should display multiple rules', () => {
    const multipleRules = [
      ...mockRules,
      {
        id: 'rule-2',
        triggerType: 'slow_query',
        channelType: 'slack',
        enabled: true,
        alertLevels: ['critical'],
      },
    ];

    render(
      <DeliveryRules
        rules={multipleRules}
        channels={mockChannels}
        triggerTypes={mockTriggerTypes}
      />
    );

    expect(screen.getByText('high_cost_query → email')).toBeInTheDocument();
    expect(screen.getByText('slow_query → slack')).toBeInTheDocument();
  });

  test('should disable form when adding rule with missing fields', () => {
    const { container } = render(
      <DeliveryRules
        rules={mockRules}
        channels={mockChannels}
        triggerTypes={mockTriggerTypes}
      />
    );

    fireEvent.click(screen.getByText('+ Add Rule'));

    const submitButton = screen.getByText('Add Rule') as HTMLButtonElement;
    expect(submitButton.disabled).toBe(true);
  });

  test('should cancel adding rule', () => {
    render(
      <DeliveryRules
        rules={mockRules}
        channels={mockChannels}
        triggerTypes={mockTriggerTypes}
      />
    );

    fireEvent.click(screen.getByText('+ Add Rule'));
    expect(screen.getByText('Cancel')).toBeInTheDocument();

    fireEvent.click(screen.getByText('Cancel'));
    expect(screen.queryByText('Add Rule')).not.toBeInTheDocument();
  });
});
