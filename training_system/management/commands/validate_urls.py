"""
Django management command to validate URL patterns and routing configuration.
"""
from django.core.management.base import BaseCommand
from django.urls import get_resolver
from django.conf import settings
import re


class Command(BaseCommand):
    help = 'Validate URL patterns and routing configuration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed URL pattern information',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Validating URL patterns...'))
        
        # Get URL resolver
        resolver = get_resolver()
        
        # Collect all URL patterns
        url_patterns = self.collect_url_patterns(resolver)
        
        # Validate patterns
        issues = self.validate_patterns(url_patterns)
        
        # Display results
        if options['verbose']:
            self.display_all_patterns(url_patterns)
        
        if issues:
            self.stdout.write(self.style.ERROR(f'Found {len(issues)} issues:'))
            for issue in issues:
                self.stdout.write(self.style.ERROR(f'  - {issue}'))
        else:
            self.stdout.write(self.style.SUCCESS('All URL patterns are valid!'))
        
        # Display summary
        self.display_summary(url_patterns)

    def collect_url_patterns(self, resolver, namespace=''):
        """Recursively collect all URL patterns."""
        patterns = []
        
        for pattern in resolver.url_patterns:
            if hasattr(pattern, 'url_patterns'):
                # This is an included URLconf
                sub_namespace = f"{namespace}:{pattern.namespace}" if pattern.namespace else namespace
                patterns.extend(self.collect_url_patterns(pattern, sub_namespace))
            else:
                # This is a regular URL pattern
                pattern_info = {
                    'pattern': str(pattern.pattern),
                    'name': pattern.name,
                    'namespace': namespace,
                    'view': self.get_view_name(pattern),
                    'full_name': f"{namespace}:{pattern.name}" if namespace and pattern.name else pattern.name,
                }
                patterns.append(pattern_info)
        
        return patterns

    def get_view_name(self, pattern):
        """Get the view name from a URL pattern."""
        if hasattr(pattern, 'callback'):
            if hasattr(pattern.callback, '__name__'):
                return pattern.callback.__name__
            elif hasattr(pattern.callback, 'view_class'):
                return pattern.callback.view_class.__name__
            else:
                return str(pattern.callback)
        return 'Unknown'

    def validate_patterns(self, patterns):
        """Validate URL patterns for common issues."""
        issues = []
        pattern_names = []
        
        for pattern in patterns:
            # Check for duplicate names
            if pattern['name'] and pattern['full_name'] in pattern_names:
                issues.append(f"Duplicate URL name: {pattern['full_name']}")
            elif pattern['name']:
                pattern_names.append(pattern['full_name'])
            
            # Check for unnamed patterns (except admin and static)
            if not pattern['name'] and not any(x in pattern['pattern'] for x in ['admin/', 'static/', 'media/', '__debug__']):
                issues.append(f"Unnamed URL pattern: {pattern['pattern']}")
            
            # Check for potentially insecure patterns
            if re.search(r'\.\*|\.\+', pattern['pattern']):
                issues.append(f"Potentially overly broad pattern: {pattern['pattern']}")
        
        return issues

    def display_all_patterns(self, patterns):
        """Display all URL patterns in detail."""
        self.stdout.write(self.style.SUCCESS('\nAll URL Patterns:'))
        self.stdout.write('-' * 80)
        
        for pattern in sorted(patterns, key=lambda x: x['pattern']):
            name = pattern['full_name'] or 'unnamed'
            self.stdout.write(
                f"Pattern: {pattern['pattern']:<30} "
                f"Name: {name:<25} "
                f"View: {pattern['view']}"
            )

    def display_summary(self, patterns):
        """Display summary statistics."""
        total_patterns = len(patterns)
        named_patterns = len([p for p in patterns if p['name']])
        unnamed_patterns = total_patterns - named_patterns
        
        namespaces = set(p['namespace'] for p in patterns if p['namespace'])
        
        self.stdout.write(self.style.SUCCESS('\nURL Configuration Summary:'))
        self.stdout.write('-' * 40)
        self.stdout.write(f"Total URL patterns: {total_patterns}")
        self.stdout.write(f"Named patterns: {named_patterns}")
        self.stdout.write(f"Unnamed patterns: {unnamed_patterns}")
        self.stdout.write(f"Namespaces: {len(namespaces)}")
        
        if namespaces:
            self.stdout.write(f"Namespace list: {', '.join(sorted(namespaces))}")