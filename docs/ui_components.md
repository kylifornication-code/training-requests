# UI Components Documentation

This document describes the reusable UI components available in the Training Request System.

## Template Tags

All template tags are available in the `training_extras` template tag library. Load them in your templates with:

```django
{% load training_extras %}
```

## Components

### Status Badges

Display status information with consistent styling and icons.

#### `status_badge` Filter
```django
{{ request.status|status_badge }}
```

#### `training_type_badge` Filter
```django
{{ request.training_type|training_type_badge }}
```

#### `role_badge` Filter
```django
{{ user.userprofile.role|role_badge }}
```

### Statistics Cards

Display key metrics in an attractive card format.

#### `stat_card` Tag
```django
{% stat_card title="Total Requests" value="42" icon="fas fa-list" color="primary" subtitle="Optional subtitle" %}
```

**Parameters:**
- `title`: Card title
- `value`: Main statistic value
- `icon`: FontAwesome icon class
- `color`: Bootstrap color variant (primary, secondary, success, etc.)
- `subtitle`: Optional subtitle text

### Action Buttons

Consistent button styling with icons.

#### `action_button` Tag
```django
{% action_button url="/create/" text="New Request" icon="fas fa-plus" variant="primary" size="lg" extra_classes="ms-2" %}
```

**Parameters:**
- `url`: Button destination URL
- `text`: Button text
- `icon`: FontAwesome icon class
- `variant`: Bootstrap button variant
- `size`: Button size (sm, lg)
- `extra_classes`: Additional CSS classes

### Page Headers

Consistent page headers with optional actions.

#### `page_header` Tag
```django
{% page_header title="Dashboard" subtitle="Welcome back!" icon="fas fa-tachometer-alt" action_url="/new/" action_text="New Request" action_icon="fas fa-plus" %}
```

### Empty States

Display when no data is available.

#### `empty_state` Tag
```django
{% empty_state title="No Requests" message="You haven't submitted any requests yet." icon="fas fa-inbox" action_url="/create/" action_text="Create First Request" %}
```

### Progress Bars

Show completion progress.

#### `progress_bar` Filter
```django
{{ completion_percentage|progress_bar:"success" }}
```

### Filter Forms

Reusable search and filter forms.

#### `filter_form` Tag
```django
{% filter_form current_filters=filters status_choices=status_choices search_enabled=True date_filter=True clear_url="/dashboard/" %}
```

### Pagination

Enhanced pagination with page information.

#### `pagination` Tag
```django
{% pagination page_obj=page_obj is_paginated=is_paginated query_params="&search=test" %}
```

### Form Fields

Consistent form field rendering with validation.

#### `form_field` Tag
```django
{% form_field field=form.title %}
```

### Loading Spinners

Show loading states.

#### `loading_spinner` Tag
```django
{% loading_spinner variant="primary" text="Loading..." show_text=True %}
```

### Confirmation Modals

User confirmation dialogs.

#### `confirm_modal` Tag
```django
{% confirm_modal modal_id="deleteModal" title="Confirm Delete" message="Are you sure?" variant="danger" confirm_text="Delete" %}
```

### Breadcrumbs

Navigation breadcrumbs.

#### `breadcrumb` Tag
```django
{% breadcrumb breadcrumbs %}
```

Breadcrumbs should be a list of dictionaries:
```python
breadcrumbs = [
    {'title': 'Home', 'url': '/', 'icon': 'fas fa-home'},
    {'title': 'Requests', 'url': '/requests/', 'icon': 'fas fa-list'},
    {'title': 'Detail', 'icon': 'fas fa-eye'}  # Last item has no URL
]
```

### Notification Badges

Show notification counts.

#### `notification_badge` Tag
```django
{% notification_badge count=pending_count variant="warning" label="pending requests" %}
```

## Utility Filters

### Currency Formatting
```django
{{ amount|currency_format:"USD" }}
```

### Division
```django
{{ total|div:count }}
```

## JavaScript Components

The `ui-components.js` file provides additional functionality:

### UIComponents Class

Automatically initialized on page load as `window.uiComponents`.

#### Methods

- `showToast(message, type)`: Show toast notifications
- `showConfirmModal(message, action)`: Show confirmation dialogs
- `animateCounter(element, target, duration)`: Animate number counters
- `formatCurrency(amount, currency)`: Format currency values
- `formatDate(date, options)`: Format dates

#### Data Attributes

- `data-confirm="message"`: Add confirmation to links/buttons
- `data-loading="Loading..."`: Show loading state on button click
- `data-auto-submit`: Auto-submit forms on select change
- `data-bs-toggle="tooltip"`: Enable Bootstrap tooltips

## CSS Classes

### Utility Classes

- `.text-truncate-2`: Truncate text to 2 lines
- `.bg-purple`: Purple background color
- `.notification-badge`: Animated notification badge
- `.status-badge`: Enhanced status badge styling
- `.hover-bg-light`: Light background on hover

### Responsive Classes

All components are mobile-responsive and work with Bootstrap's grid system.

## Best Practices

1. **Consistency**: Use the provided components for consistent UI
2. **Accessibility**: Components include proper ARIA labels and semantic HTML
3. **Performance**: Components are optimized for fast rendering
4. **Mobile-First**: All components work on mobile devices
5. **Customization**: Use CSS custom properties for theme customization

## Examples

See `templates/components/example_usage.html` for comprehensive usage examples.