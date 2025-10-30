from django import template
from django.utils.safestring import mark_safe
from django.utils.html import format_html

register = template.Library()

@register.filter
def div(value, arg):
    """Divide value by arg"""
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError, TypeError):
        return 0

@register.filter
def status_badge(status):
    """Generate a Bootstrap badge for training request status"""
    status_config = {
        'PENDING': {
            'class': 'bg-warning text-dark',
            'icon': 'fas fa-clock',
            'text': 'Pending'
        },
        'APPROVED': {
            'class': 'bg-success',
            'icon': 'fas fa-check',
            'text': 'Approved'
        },
        'DENIED': {
            'class': 'bg-danger',
            'icon': 'fas fa-times',
            'text': 'Denied'
        },
        'COMPLETED': {
            'class': 'bg-primary',
            'icon': 'fas fa-graduation-cap',
            'text': 'Completed'
        }
    }
    
    config = status_config.get(status, {
        'class': 'bg-secondary',
        'icon': 'fas fa-question',
        'text': status
    })
    
    return format_html(
        '<span class="badge {} status-badge"><i class="{} me-1"></i>{}</span>',
        config['class'],
        config['icon'],
        config['text']
    )

@register.filter
def training_type_badge(training_type):
    """Generate a Bootstrap badge for training type"""
    type_config = {
        'CONFERENCE': {
            'class': 'bg-info',
            'icon': 'fas fa-users',
            'text': 'Conference'
        },
        'COURSE': {
            'class': 'bg-success',
            'icon': 'fas fa-book',
            'text': 'Course'
        },
        'CERTIFICATION': {
            'class': 'bg-warning text-dark',
            'icon': 'fas fa-certificate',
            'text': 'Certification'
        },
        'WORKSHOP': {
            'class': 'bg-purple text-white',
            'icon': 'fas fa-tools',
            'text': 'Workshop'
        }
    }
    
    config = type_config.get(training_type, {
        'class': 'bg-secondary',
        'icon': 'fas fa-tag',
        'text': training_type
    })
    
    return format_html(
        '<span class="badge {}"><i class="{} me-1"></i>{}</span>',
        config['class'],
        config['icon'],
        config['text']
    )

@register.filter
def role_badge(role):
    """Generate a Bootstrap badge for user role"""
    role_config = {
        'TEAM_MEMBER': {
            'class': 'bg-secondary',
            'icon': 'fas fa-user',
            'text': 'Team Member'
        },
        'LEADERSHIP': {
            'class': 'bg-primary',
            'icon': 'fas fa-crown',
            'text': 'Leadership'
        },
        'ADMIN': {
            'class': 'bg-danger',
            'icon': 'fas fa-shield-alt',
            'text': 'Administrator'
        }
    }
    
    config = role_config.get(role, {
        'class': 'bg-secondary',
        'icon': 'fas fa-user',
        'text': role
    })
    
    return format_html(
        '<span class="badge role-badge {}"><i class="{} me-1"></i>{}</span>',
        config['class'],
        config['icon'],
        config['text']
    )

@register.filter
def progress_bar(percentage, variant='primary'):
    """Generate a Bootstrap progress bar"""
    percentage = max(0, min(100, float(percentage or 0)))
    
    return format_html(
        '<div class="progress"><div class="progress-bar bg-{}" role="progressbar" style="width: {}%" aria-valuenow="{}" aria-valuemin="0" aria-valuemax="100">{:.0f}%</div></div>',
        variant,
        percentage,
        percentage,
        percentage
    )

@register.filter
def currency_format(amount, currency='USD'):
    """Format currency amount"""
    try:
        amount = float(amount)
        if currency == 'USD':
            return f'${amount:,.2f}'
        else:
            return f'{amount:,.2f} {currency}'
    except (ValueError, TypeError):
        return f'0.00 {currency}'

@register.inclusion_tag('components/stat_card.html')
def stat_card(title, value, icon, color='primary', subtitle=None):
    """Render a statistics card component"""
    return {
        'title': title,
        'value': value,
        'icon': icon,
        'color': color,
        'subtitle': subtitle
    }

@register.inclusion_tag('components/action_button.html')
def action_button(url, text, icon, variant='primary', size='', extra_classes=''):
    """Render an action button component"""
    return {
        'url': url,
        'text': text,
        'icon': icon,
        'variant': variant,
        'size': size,
        'extra_classes': extra_classes
    }

@register.inclusion_tag('components/empty_state.html')
def empty_state(title, message, icon='fas fa-inbox', action_url=None, action_text=None):
    """Render an empty state component"""
    return {
        'title': title,
        'message': message,
        'icon': icon,
        'action_url': action_url,
        'action_text': action_text
    }

@register.inclusion_tag('components/notification_badge.html')
def notification_badge(count, variant='warning', label='notifications'):
    """Render a notification badge component"""
    return {
        'count': count,
        'variant': variant,
        'label': label
    }

@register.inclusion_tag('components/page_header.html')
def page_header(title, subtitle=None, icon=None, action_url=None, action_text=None, action_icon=None, action_variant='primary'):
    """Render a page header component"""
    return {
        'title': title,
        'subtitle': subtitle,
        'icon': icon,
        'action_url': action_url,
        'action_text': action_text,
        'action_icon': action_icon,
        'action_variant': action_variant
    }

@register.inclusion_tag('components/filter_form.html')
def filter_form(current_filters=None, status_choices=None, search_enabled=True, date_filter=False, 
                search_placeholder='Search...', form_id='filterForm', clear_url=''):
    """Render a filter form component"""
    has_filters = False
    if current_filters:
        has_filters = any([
            current_filters.get('search'),
            current_filters.get('status'),
            current_filters.get('date_from'),
            current_filters.get('date_to')
        ])
    
    return {
        'current_filters': current_filters or {},
        'status_choices': status_choices,
        'search_enabled': search_enabled,
        'date_filter': date_filter,
        'search_placeholder': search_placeholder,
        'form_id': form_id,
        'clear_url': clear_url,
        'has_filters': has_filters
    }

@register.inclusion_tag('components/pagination.html')
def pagination(page_obj, is_paginated, query_params='', aria_label='Page navigation'):
    """Render pagination component"""
    return {
        'page_obj': page_obj,
        'is_paginated': is_paginated,
        'query_params': query_params,
        'aria_label': aria_label
    }

@register.inclusion_tag('components/form_field.html')
def form_field(field):
    """Render a form field component"""
    return {
        'field': field
    }

@register.inclusion_tag('components/loading_spinner.html')
def loading_spinner(variant='primary', text='Loading...', show_text=False, spinner_id='loadingSpinner'):
    """Render a loading spinner component"""
    return {
        'variant': variant,
        'text': text,
        'show_text': show_text,
        'spinner_id': spinner_id
    }

@register.inclusion_tag('components/confirm_modal.html')
def confirm_modal(modal_id='confirmModal', title='Confirm Action', message='Are you sure?', 
                  variant='danger', confirm_text='Confirm', icon=None, confirm_icon=None):
    """Render a confirmation modal component"""
    return {
        'modal_id': modal_id,
        'title': title,
        'message': message,
        'variant': variant,
        'confirm_text': confirm_text,
        'icon': icon,
        'confirm_icon': confirm_icon
    }

@register.inclusion_tag('components/breadcrumb.html')
def breadcrumb(breadcrumbs):
    """Render a breadcrumb navigation component"""
    return {
        'breadcrumbs': breadcrumbs
    }