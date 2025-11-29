/**
 * Simple textarea syntax highlighter using highlight.js
 * Replaces the problematic highlighted-code library
 */

class SimpleCodeHighlighter {
    constructor(textarea, language) {
        this.textarea = textarea;
        this.language = language;
        this.pre = null;
        this.code = null;
        this.init();
    }

    init() {
        // Create the highlighting overlay
        this.pre = document.createElement('pre');
        this.code = document.createElement('code');

        if (this.language) {
            this.code.className = `language-${this.language}`;
        } else {
            this.code.className = 'language-plaintext';
        }

        this.pre.appendChild(this.code);
        this.pre.className = 'simple-highlighter-overlay';

        // Style the overlay to match the textarea
        Object.assign(this.pre.style, {
            position: 'absolute',
            top: '0',
            left: '0',
            width: '100%',
            height: '100%',
            margin: '0',
            padding: this.textarea.style.padding || '8px',
            border: this.textarea.style.border || '1px solid #ccc',
            borderRadius: this.textarea.style.borderRadius || '4px',
            backgroundColor: this.textarea.style.backgroundColor || 'white',
            fontFamily: this.textarea.style.fontFamily || 'monospace',
            fontSize: this.textarea.style.fontSize || '14px',
            lineHeight: this.textarea.style.lineHeight || '1.4',
            color: 'transparent',
            pointerEvents: 'none',
            zIndex: '1',
            overflow: 'hidden',
            whiteSpace: 'pre-wrap',
            wordWrap: 'break-word'
        });

        // Position the overlay over the textarea
        this.updatePosition();

        // Insert the overlay after the textarea
        this.textarea.parentNode.insertBefore(this.pre, this.textarea.nextSibling);

        // Initial highlight
        this.highlight();

        // Bind events
        this.textarea.addEventListener('input', () => this.highlight());
        this.textarea.addEventListener('scroll', () => this.syncScroll());
        this.textarea.addEventListener('keydown', (e) => this.handleKeydown(e));

        // Update position on window resize
        window.addEventListener('resize', () => this.updatePosition());
    }

    updatePosition() {
        const rect = this.textarea.getBoundingClientRect();
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;

        Object.assign(this.pre.style, {
            top: (rect.top + scrollTop) + 'px',
            left: (rect.left + scrollLeft) + 'px',
            width: rect.width + 'px',
            height: rect.height + 'px'
        });
    }

    highlight() {
        const text = this.textarea.value;
        if (this.language && window.hljs) {
            try {
                const highlighted = window.hljs.highlight(text, { language: this.language });
                this.code.innerHTML = highlighted.value;
            } catch (e) {
                // Fallback to plain text if highlighting fails
                this.code.textContent = text;
                this.code.className = 'language-plaintext';
            }
        } else {
            this.code.textContent = text;
        }
    }

    syncScroll() {
        this.pre.scrollTop = this.textarea.scrollTop;
        this.pre.scrollLeft = this.textarea.scrollLeft;
    }

    handleKeydown(e) {
        // Handle Tab key for indentation
        if (e.key === 'Tab') {
            e.preventDefault();
            const start = this.textarea.selectionStart;
            const end = this.textarea.selectionEnd;

            // Insert tab character
            this.textarea.value = this.textarea.value.substring(0, start) + '\t' + this.textarea.value.substring(end);
            this.textarea.selectionStart = this.textarea.selectionEnd = start + 1;

            // Trigger highlight update
            this.highlight();
        }
    }

    destroy() {
        if (this.pre && this.pre.parentNode) {
            this.pre.parentNode.removeChild(this.pre);
        }
    }
}

// Auto-initialize for textareas with data-lang attribute
document.addEventListener('DOMContentLoaded', function() {
    // Initialize textareas with language attribute
    document.querySelectorAll('textarea[language]').forEach(textarea => {
        const language = textarea.getAttribute('language');
        new SimpleCodeHighlighter(textarea, language);
    });

    // Also check for is="highlighted-code" attribute for backward compatibility
    document.querySelectorAll('textarea[is="highlighted-code"]').forEach(textarea => {
        const language = textarea.getAttribute('language');
        new SimpleCodeHighlighter(textarea, language);
    });
});

// Make it globally available
window.SimpleCodeHighlighter = SimpleCodeHighlighter;