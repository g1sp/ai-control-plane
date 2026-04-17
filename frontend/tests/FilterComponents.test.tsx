/**
 * Tests for filter UI components
 */

import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import MultiSelect from "../src/components/MultiSelect";
import RangeSlider from "../src/components/RangeSlider";
import DateRangePicker from "../src/components/DateRangePicker";

describe("MultiSelect Component", () => {
  const options = ["user1", "user2", "user3"];

  test("should render with label and placeholder", () => {
    render(
      <MultiSelect
        label="Select Users"
        placeholder="Choose users..."
        options={options}
        selected={null}
        onChange={() => {}}
      />
    );

    expect(screen.getByText("Select Users")).toBeInTheDocument();
    expect(screen.getByText("Choose users...")).toBeInTheDocument();
  });

  test("should display number of selected items", () => {
    render(
      <MultiSelect
        label="Select Users"
        options={options}
        selected={["user1", "user2"]}
        onChange={() => {}}
      />
    );

    expect(screen.getByText("2 selected")).toBeInTheDocument();
  });

  test("should toggle dropdown on button click", async () => {
    const { rerender } = render(
      <MultiSelect
        label="Select Users"
        options={options}
        selected={null}
        onChange={() => {}}
      />
    );

    const button = screen.getByRole("button");
    fireEvent.click(button);

    await waitFor(() => {
      expect(screen.getByText("Select All")).toBeInTheDocument();
    });
  });

  test("should select and deselect items", async () => {
    const handleChange = jest.fn();

    const { rerender } = render(
      <MultiSelect
        label="Select Users"
        options={options}
        selected={null}
        onChange={handleChange}
      />
    );

    // Open dropdown
    const button = screen.getByRole("button");
    fireEvent.click(button);

    // Select item
    await waitFor(() => {
      const user1Checkbox = screen.getByRole("checkbox", { name: /user1/i });
      fireEvent.click(user1Checkbox);
    });

    expect(handleChange).toHaveBeenCalledWith(["user1"]);
  });

  test("should select all items", async () => {
    const handleChange = jest.fn();

    render(
      <MultiSelect
        label="Select Users"
        options={options}
        selected={null}
        onChange={handleChange}
      />
    );

    // Open dropdown
    fireEvent.click(screen.getByRole("button"));

    // Click Select All
    await waitFor(() => {
      const selectAll = screen.getByText("Select All");
      fireEvent.click(selectAll);
    });

    expect(handleChange).toHaveBeenCalledWith(options);
  });

  test("should clear selection", async () => {
    const handleChange = jest.fn();

    render(
      <MultiSelect
        label="Select Users"
        options={options}
        selected={["user1"]}
        onChange={handleChange}
      />
    );

    const clearButton = screen.getByText("✕");
    fireEvent.click(clearButton);

    expect(handleChange).toHaveBeenCalledWith(null);
  });
});

describe("RangeSlider Component", () => {
  test("should render with label", () => {
    render(
      <RangeSlider
        label="Cost Range"
        min={0}
        max={1000}
        value={null}
        onChange={() => {}}
      />
    );

    expect(screen.getByText("Cost Range")).toBeInTheDocument();
  });

  test("should display min and max inputs", () => {
    render(
      <RangeSlider
        label="Cost Range"
        min={0}
        max={1000}
        value={[100, 500]}
        onChange={() => {}}
      />
    );

    const inputs = screen.getAllByRole("spinbutton");
    expect(inputs).toHaveLength(2);
    expect(inputs[0]).toHaveValue(100);
    expect(inputs[1]).toHaveValue(500);
  });

  test("should update range when input changes", () => {
    const handleChange = jest.fn();

    render(
      <RangeSlider
        label="Cost Range"
        min={0}
        max={1000}
        value={[100, 500]}
        onChange={handleChange}
      />
    );

    const minInput = screen.getAllByRole("spinbutton")[0];
    fireEvent.change(minInput, { target: { value: "200" } });

    expect(handleChange).toHaveBeenCalledWith([200, 500]);
  });

  test("should show reset button when value is active", () => {
    render(
      <RangeSlider
        label="Cost Range"
        min={0}
        max={1000}
        value={[100, 500]}
        onChange={() => {}}
      />
    );

    expect(screen.getByText("Reset")).toBeInTheDocument();
  });

  test("should call onClear when reset clicked", () => {
    const handleClear = jest.fn();

    render(
      <RangeSlider
        label="Cost Range"
        min={0}
        max={1000}
        value={[100, 500]}
        onChange={() => {}}
        onClear={handleClear}
      />
    );

    fireEvent.click(screen.getByText("Reset"));

    expect(handleClear).toHaveBeenCalled();
  });

  test("should prevent min from exceeding max", () => {
    const handleChange = jest.fn();

    render(
      <RangeSlider
        label="Cost Range"
        min={0}
        max={1000}
        value={[100, 500]}
        onChange={handleChange}
      />
    );

    const minInput = screen.getAllByRole("spinbutton")[0];
    fireEvent.change(minInput, { target: { value: "600" } });

    // Should be clamped to max (500)
    expect(handleChange).toHaveBeenCalledWith([500, 500]);
  });

  test("should display unit in label", () => {
    render(
      <RangeSlider
        label="Cost Range"
        unit="$"
        min={0}
        max={1000}
        value={[100, 500]}
        onChange={() => {}}
      />
    );

    expect(screen.getByText(/\$ - \$/)).toBeInTheDocument();
  });
});

describe("DateRangePicker Component", () => {
  test("should render with label", () => {
    render(
      <DateRangePicker
        label="Date Range"
        startDate="2026-04-01"
        endDate="2026-04-30"
        onChange={() => {}}
      />
    );

    expect(screen.getByText("Date Range")).toBeInTheDocument();
  });

  test("should display start and end date inputs", () => {
    render(
      <DateRangePicker
        label="Date Range"
        startDate="2026-04-01"
        endDate="2026-04-30"
        onChange={() => {}}
      />
    );

    const inputs = screen.getAllByRole("textbox");
    expect(inputs).toHaveLength(2);
    expect(inputs[0]).toHaveValue("2026-04-01");
    expect(inputs[1]).toHaveValue("2026-04-30");
  });

  test("should call onChange when dates change", () => {
    const handleChange = jest.fn();

    render(
      <DateRangePicker
        label="Date Range"
        startDate="2026-04-01"
        endDate="2026-04-30"
        onChange={handleChange}
      />
    );

    const startInput = screen.getAllByRole("textbox")[0];
    fireEvent.change(startInput, { target: { value: "2026-04-05" } });

    expect(handleChange).toHaveBeenCalledWith("2026-04-05", "2026-04-30");
  });

  test("should display formatted date range", () => {
    render(
      <DateRangePicker
        label="Date Range"
        startDate="2026-04-01"
        endDate="2026-04-30"
        onChange={() => {}}
      />
    );

    // Should show formatted dates
    expect(screen.getByText(/April 1, 2026.*April 30, 2026/)).toBeInTheDocument();
  });

  test("should have clear button when onClear provided", () => {
    const handleClear = jest.fn();

    render(
      <DateRangePicker
        label="Date Range"
        startDate="2026-04-01"
        endDate="2026-04-30"
        onChange={() => {}}
        onClear={handleClear}
      />
    );

    fireEvent.click(screen.getByText("Clear"));

    expect(handleClear).toHaveBeenCalled();
  });
});
