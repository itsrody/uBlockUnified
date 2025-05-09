import sqlite3
import re
import os

class UBlockRuleConverter:
    def __init__(self, db_path='ublock_rules_dictionary.db'):
        """Initialize the UBlock Origin Rules Dictionary Database."""
        self.db_path = db_path
        self.create_database()
        self.populate_database()
    
    def create_database(self):
        """Create the database schema if it doesn't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS rule_types (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            ublock_support INTEGER NOT NULL
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS adblocker_sources (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT NOT NULL
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS rule_patterns (
            id INTEGER PRIMARY KEY,
            source_id INTEGER NOT NULL,
            rule_type_id INTEGER NOT NULL,
            pattern TEXT NOT NULL,
            example TEXT NOT NULL,
            FOREIGN KEY (source_id) REFERENCES adblocker_sources(id),
            FOREIGN KEY (rule_type_id) REFERENCES rule_types(id)
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversion_rules (
            id INTEGER PRIMARY KEY,
            source_pattern_id INTEGER NOT NULL,
            ublock_pattern TEXT NOT NULL,
            conversion_function TEXT,
            notes TEXT,
            FOREIGN KEY (source_pattern_id) REFERENCES rule_patterns(id)
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def populate_database(self):
        """Populate the database with rule types, sources, patterns, and conversions."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Populate rule types
        rule_types = [
            (1, 'Basic URL Blocking', 'Simple URL pattern blocking', 1),
            (2, 'Domain-specific Blocking', 'Rules that apply to specific domains', 1),
            (3, 'Element Hiding', 'CSS-based element hiding', 1),
            (4, 'Exception Rules', 'Whitelisting rules', 1),
            (5, 'Regular Expression', 'RegEx-based rules', 1),
            (6, 'Resource Replacement', 'Replacing resources with alternatives', 1),
            (7, 'Scriptlet Injection', 'JavaScript injection for countering anti-adblock', 1),
            (8, 'HTML Filtering', 'Filtering HTML content before rendering', 1),
            (9, 'Hosts File Format', 'Rules in hosts file format', 1),
            (10, 'DNS-level Blocking', 'Network-level DNS blocking', 0),
            (11, 'Extended CSS', 'Advanced CSS selectors beyond standard', 1),
            (12, 'Network Filter Options', 'Additional options for network filters', 1),
            (13, 'Dynamic Rules', 'Rules that change based on conditions', 1),
            (14, 'URL Parameter Removal', 'Removing tracking parameters from URLs', 1),
            (15, 'Redirect Rules', 'Redirecting requests to alternative resources', 1)
        ]
        
        cursor.execute('DELETE FROM rule_types')
        cursor.executemany('INSERT INTO rule_types VALUES (?, ?, ?, ?)', rule_types)
        
        # Populate adblocker sources
        sources = [
            (1, 'AdBlock Plus', 'The original major adblocker'),
            (2, 'AdGuard', 'Advanced adblocker with extended functionality'),
            (3, 'Ghostery', 'Tracker-focused blocking tool'),
            (4, 'ClearURLs', 'Tool focused on URL parameter cleaning'),
            (5, 'Privacy Badger', 'Learning-based privacy tool'),
            (6, 'Pi-hole', 'Network-level DNS blocker'),
            (7, 'uBlock Origin', 'uBlock Origin native format'),
            (8, 'Hosts File', 'Standard hosts file format')
        ]
        
        cursor.execute('DELETE FROM adblocker_sources')
        cursor.executemany('INSERT INTO adblocker_sources VALUES (?, ?, ?)', sources)
        
        # Populate rule patterns
        rule_patterns = [
            # AdBlock Plus patterns
            (1, 1, 1, '||example.com^', 'Blocks requests to example.com and its subdomains'),
            (2, 1, 3, '##.ad-class', 'Hides elements with class "ad-class" on all sites'),
            (3, 1, 3, 'example.com##.ad-class', 'Hides elements with class "ad-class" on example.com'),
            (4, 1, 4, '@@||example.com^', 'Whitelists requests to example.com'),
            (5, 1, 5, '/ads/[0-9]{3}x[0-9]{3}/', 'Blocks ads with dimension patterns like 300x250'),
            (6, 1, 12, '||example.com^$third-party', 'Blocks example.com when loaded as third-party'),
            
            # AdGuard patterns
            (7, 2, 3, 'example.com#$#.ad-class { display: none !important; }', 'CSS-based element hiding'),
            (8, 2, 7, 'example.com#%#//scriptlet("abort-on-property-read", "adBlockDetected")', 'AdGuard scriptlet injection'),
            (9, 2, 11, 'example.com##.ad:has(.banner)', 'Extended CSS selector with :has()'),
            (10, 2, 14, '||example.com^$removeparam=utm_source', 'Removes utm_source parameter'),
            (11, 2, 15, '||ads.example.com^$redirect=nooptext', 'Redirects ads to empty text'),
            
            # Ghostery patterns
            (12, 3, 1, 'example.com/tracker.js', 'Blocks specific tracker script'),
            (13, 3, 2, '*example.com*', 'Blocks all requests containing example.com'),
            
            # ClearURLs patterns
            (14, 4, 14, 'example.com/?utm_*', 'Removes all UTM parameters'),
            (15, 4, 14, '{utm_source}', 'Parameter removal in ClearURLs syntax'),
            
            # Privacy Badger patterns (conceptual, as Privacy Badger learns rather than using fixed rules)
            (16, 5, 2, 'example.com/*', 'Domain-based blocking learned by Privacy Badger'),
            
            # Pi-hole patterns
            (17, 6, 9, 'ads.example.com', 'Blocks ads.example.com at DNS level'),
            (18, 6, 9, '0.0.0.0 ads.example.com', 'Standard hosts file format used by Pi-hole'),
            
            # Hosts file format
            (19, 8, 9, '127.0.0.1 ads.example.com', 'Standard hosts file blocking format'),
            
            # uBlock Origin specific patterns (for reference)
            (20, 7, 1, '||example.com^', 'uBlock format for domain blocking'),
            (21, 7, 3, 'example.com##.ad-class', 'uBlock element hiding'),
            (22, 7, 7, 'example.com##+js(aopr, adBlockDetected)', 'uBlock scriptlet injection'),
            (23, 7, 8, 'example.com##^script:has-text(ads)', 'uBlock HTML filtering'),
            (24, 7, 15, '||ads.example.com^$redirect=1x1.gif', 'uBlock redirect rule')
        ]
        
        cursor.execute('DELETE FROM rule_patterns')
        cursor.executemany('INSERT INTO rule_patterns VALUES (?, ?, ?, ?, ?)', rule_patterns)
        
        # Populate conversion rules
        conversion_rules = [
            # AdBlock Plus to uBlock Origin
            (1, 1, '||example.com^', None, 'Direct compatibility'),
            (2, 2, '##.ad-class', None, 'Direct compatibility'),
            (3, 3, 'example.com##.ad-class', None, 'Direct compatibility'),
            (4, 4, '@@||example.com^', None, 'Direct compatibility'),
            (5, 5, '/ads/[0-9]{3}x[0-9]{3}/', None, 'Direct compatibility'),
            (6, 6, '||example.com^$third-party', None, 'Direct compatibility'),
            
            # AdGuard to uBlock Origin
            (7, 7, 'example.com##.ad-class', 'convert_adguard_css_to_ublock', 'Convert to standard element hiding'),
            (8, 8, 'example.com##+js(abort-on-property-read, adBlockDetected)', 'convert_adguard_scriptlet_to_ublock', 'Convert to uBO scriptlet syntax'),
            (9, 9, 'example.com##.ad:has(.banner)', None, 'Direct compatibility with modern uBO'),
            (10, 10, '||example.com^$removeparam=utm_source', None, 'Direct compatibility with modern uBO'),
            (11, 11, '||ads.example.com^$redirect=nooptext', 'convert_adguard_redirect_to_ublock', 'May need resource name adjustment'),
            
            # Ghostery to uBlock Origin
            (12, 12, '||example.com/tracker.js^', 'convert_ghostery_to_ublock', 'Convert to uBO network filter syntax'),
            (13, 13, '||example.com^', 'convert_ghostery_wildcard_to_ublock', 'Convert wildcard to uBO syntax'),
            
            # ClearURLs to uBlock Origin
            (14, 14, '||example.com^$removeparam=/utm_.*/i', 'convert_clearurls_to_ublock_removeparam', 'Convert to removeparam syntax'),
            (15, 15, '||*$removeparam=utm_source', 'convert_clearurls_param_to_ublock', 'Convert to removeparam syntax'),
            
            # Privacy Badger to uBlock Origin (conceptual)
            (16, 16, '||example.com^$all', 'privacy_badger_domain_to_ublock', 'Convert learned domain to strict blocking'),
            
            # Pi-hole to uBlock Origin
            (17, 17, '||ads.example.com^', 'convert_pihole_to_ublock', 'Convert DNS rule to network filter'),
            (18, 18, '||ads.example.com^', 'convert_hosts_to_ublock', 'Convert hosts format to network filter'),
            
            # Hosts file to uBlock Origin
            (19, 19, '||ads.example.com^', 'convert_hosts_to_ublock', 'Convert hosts format to network filter')
        ]
        
        cursor.execute('DELETE FROM conversion_rules')
        cursor.executemany('INSERT INTO conversion_rules VALUES (?, ?, ?, ?, ?)', conversion_rules)
        
        conn.commit()
        conn.close()

    def get_rule_types(self):
        """Get all rule types with support information."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT id, name, description, ublock_support
        FROM rule_types
        ORDER BY id
        ''')
        
        rule_types = cursor.fetchall()
        conn.close()
        
        return rule_types
    
    def get_adblocker_sources(self):
        """Get all adblocker sources."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT id, name, description
        FROM adblocker_sources
        ORDER BY id
        ''')
        
        sources = cursor.fetchall()
        conn.close()
        
        return sources
    
    def get_conversion_rules_by_source(self, source_id):
        """Get conversion rules for a specific source."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT rp.pattern, rp.example, cr.ublock_pattern, cr.conversion_function, cr.notes
        FROM conversion_rules cr
        JOIN rule_patterns rp ON cr.source_pattern_id = rp.id
        WHERE rp.source_id = ?
        ''', (source_id,))
        
        rules = cursor.fetchall()
        conn.close()
        
        return rules
    
    def convert_rule(self, rule, source_name):
        """Convert a rule from the specified source to uBlock Origin syntax."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get source ID
        cursor.execute('SELECT id FROM adblocker_sources WHERE name = ?', (source_name,))
        source_id = cursor.fetchone()
        
        if not source_id:
            conn.close()
            return None, "Source not found"
        
        source_id = source_id[0]
        
        # Get all patterns for this source
        cursor.execute('''
        SELECT rp.id, rp.pattern, cr.ublock_pattern, cr.conversion_function
        FROM rule_patterns rp
        JOIN conversion_rules cr ON rp.id = cr.source_pattern_id
        WHERE rp.source_id = ?
        ''', (source_id,))
        
        patterns = cursor.fetchall()
        conn.close()
        
        # Try to find a matching pattern
        for pattern_id, pattern, ublock_pattern, conversion_function in patterns:
            # Convert regex pattern to actual regex
            pattern_regex = self._pattern_to_regex(pattern)
            if re.match(pattern_regex, rule):
                if conversion_function:
                    # If there's a conversion function defined, we'd call it
                    # Here we're simulating the conversion logic
                    return self._apply_conversion(rule, conversion_function, pattern, ublock_pattern), "Converted"
                else:
                    # Direct compatibility
                    return rule, "Direct compatibility"
        
        return rule, "No specific conversion rule found, assuming compatibility"
    
    def _pattern_to_regex(self, pattern):
        """Convert a pattern to a regular expression for matching."""
        # Escape special regex characters except * which we'll convert to .*
        special_chars = '.^$+?()[]{}|\\/'
        regex = ''
        for char in pattern:
            if char == '*':
                regex += '.*'
            elif char in special_chars:
                regex += '\\' + char
            else:
                regex += char
        return '^' + regex + '$'
    
    def _apply_conversion(self, rule, conversion_function, pattern, ublock_pattern):
        """Apply a conversion function to transform a rule."""
        # In a real implementation, this would dynamically call the function
        # For now, we'll implement some common conversions directly
        
        if conversion_function == 'convert_adguard_css_to_ublock':
            # Convert AdGuard CSS rules to uBlock
            return re.sub(r'#\$#(.*) \{ display: none !important; \}', r'##\1', rule)
        
        elif conversion_function == 'convert_adguard_scriptlet_to_ublock':
            # Convert AdGuard scriptlet to uBlock scriptlet
            match = re.search(r'#%#//scriptlet\("([^"]+)", "([^"]+)"\)', rule)
            if match:
                scriptlet_name = match.group(1)
                scriptlet_arg = match.group(2)
                domain = rule.split('#')[0]
                
                # Map AdGuard scriptlet names to uBlock names
                scriptlet_map = {
                    'abort-on-property-read': 'aopr',
                    'abort-on-property-write': 'aopw',
                    'abort-current-inline-script': 'acis',
                    'set-constant': 'set',
                    'json-prune': 'json-prune'
                }
                
                ubo_scriptlet = scriptlet_map.get(scriptlet_name, scriptlet_name)
                return f"{domain}##+js({ubo_scriptlet}, {scriptlet_arg})"
            return rule
        
        elif conversion_function == 'convert_adguard_redirect_to_ublock':
            # Convert AdGuard redirect to uBlock redirect
            # Map resource names if needed
            resource_map = {
                'nooptext': '1x1.gif',
                'noopjs': 'noop.js',
                'noopframe': 'empty.html'
            }
            
            for adguard_res, ubo_res in resource_map.items():
                if adguard_res in rule:
                    return rule.replace(adguard_res, ubo_res)
            return rule
        
        elif conversion_function == 'convert_ghostery_to_ublock':
            # Convert Ghostery rule to uBlock syntax
            if not rule.startswith('||'):
                return f"||{rule}^"
            return rule
        
        elif conversion_function == 'convert_ghostery_wildcard_to_ublock':
            # Convert Ghostery wildcard rule to uBlock syntax
            return rule.replace('*example.com*', '||example.com^')
        
        elif conversion_function == 'convert_clearurls_to_ublock_removeparam':
            # Convert ClearURLs rule to uBlock removeparam
            domain = rule.split('/?')[0]
            param = rule.split('/?')[1].replace('*', '')
            return f"{domain}$removeparam=/{param}.*/i"
        
        elif conversion_function in ['convert_hosts_to_ublock', 'convert_pihole_to_ublock']:
            # Convert hosts file or Pi-hole rule to uBlock
            # Remove IP address if present
            domain = re.sub(r'^(0\.0\.0\.0|127\.0\.0\.1)\s+', '', rule).strip()
            return f"||{domain}^"
        
        # Default: return the uBlock pattern with domain from original rule
        domain_match = re.match(r'^([^#^$]*)', rule)
        if domain_match:
            domain = domain_match.group(1)
            return ublock_pattern.replace('example.com', domain)
        
        return ublock_pattern

def create_database():
    """Create and populate the uBlock rules dictionary database."""
    converter = UBlockRuleConverter()
    print(f"Database created at {converter.db_path}")
    
    # Show some examples of the database content
    rule_types = converter.get_rule_types()
    print("\nRule Types:")
    for rule_type in rule_types[:5]:  # Show first 5
        print(f"{rule_type[0]}: {rule_type[1]} - {rule_type[2]} (uBlock Support: {'Yes' if rule_type[3] else 'No'})")
    
    sources = converter.get_adblocker_sources()
    print("\nAdblocker Sources:")
    for source in sources:
        print(f"{source[0]}: {source[1]} - {source[2]}")
    
    # Example conversion
    print("\nExample conversions:")
    example_rules = [
        ("ads.example.com", "Pi-hole"),
        ("127.0.0.1 track.example.com", "Hosts File"),
        ("example.com#$#.ad-class { display: none !important; }", "AdGuard"),
        ("example.com#%#//scriptlet(\"abort-on-property-read\", \"adBlockDetected\")", "AdGuard"),
        ("||example.com^$removeparam=utm_source", "AdGuard"),
        ("example.com/?utm_*", "ClearURLs")
    ]
    
    for rule, source in example_rules:
        converted, status = converter.convert_rule(rule, source)
        print(f"Original ({source}): {rule}")
        print(f"Converted: {converted} - {status}\n")

if __name__ == "__main__":
    create_database()
