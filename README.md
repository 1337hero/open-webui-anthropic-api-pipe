# Anthropic Claude API Pipeline for Open WebUI

A clean, secure Anthropic Claude integration for Open WebUI. Built with DHH-inspired principles: simple, expressive, and secure by defaultnot security theater.

This pipeline provides seamless access to all Claude models with essential security features and zero configuration overhead.

## Features

### Security (Real Protection, Not Theater)
 **SSRF Protection** - Validates URLs, blocks private networks and metadata endpoints
 **Input Validation** - Prevents crashes from malformed data
 **Secure Error Handling** - User-friendly messages, no information disclosure
 **Image Size Validation** - Enforces Anthropic's 5MB limit per image

### Core Functionality
 **Streaming Support** - Real-time response streaming
 **Multimodal** - Text and image processing
 **Retry Logic** - Automatic retry with exponential backoff
 **All Claude Models** - Full model family support

## Supported Models

### Claude 4 Family (Latest)
- **claude-sonnet-4-5-20250929** - Best balance of intelligence, speed, and cost
- **claude-haiku-4-5-20251001** - Fastest responses with near-frontier intelligence
- **claude-opus-4-1-20250805** - Specialized reasoning for complex tasks

### Claude 3.7
- **claude-3-7-sonnet-20250219** - Enhanced capabilities with extended thinking

### Claude 3.5 Family
- **claude-3-5-sonnet-20241022** - Strong general-purpose model
- **claude-3-5-haiku-20241022** - Fast and cost-effective

### Claude 3 Family
- **claude-3-opus-20240229** - Previous generation flagship
- **claude-3-sonnet-20240229** - Balanced performance
- **claude-3-haiku-20240307** - Speed-optimized

## Installation

### Prerequisites
- Open WebUI 0.5.0 or later
- Python 3.11+
- Anthropic API key ([get one here](https://console.anthropic.com/))

### Step 1: Get an Anthropic API Key
1. Sign up at [console.anthropic.com](https://console.anthropic.com/)
2. Navigate to API Keys
3. Create a new API key (starts with `sk-ant-`)

### Step 2: Install the Pipeline

Go here: https://openwebui.com/f/1337hero/anthropic_claude_api_connection

### Step 3: Configure Your API Key
The pipeline has exactly **one** configuration option:

**Open WebUI Settings**
1. Go to **Admin Panel** � **Settings** � **Functions**
2. Find "Anthropic Claude API Connection"
3. Click the settings/valve icon
4. Enter your API key
5. Save


| Setting | Description | Required |
|---------|-------------|----------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key | Yes |

That's it. No unnecessary knobs, no feature flags, no complexity.

## Security Model

### What We Protect Against
1. **SSRF Attacks** - URL validation prevents access to internal networks
2. **DoS via Large Images** - Enforces Anthropic's 5MB per-image limit
3. **Information Disclosure** - Error messages are sanitized
4. **Malformed Requests** - Input validation prevents crashes

### Security by Default
- HTTPS-only connections
- Safe error handling (no stack traces exposed)
- Private IP blocking for URL images
- Cloud metadata endpoint protection

## Error Handling

User-friendly error messages:
- `ANTHROPIC_API_KEY not configured` - Add your API key in pipeline settings
- `Invalid API key` - Check your API key is correct
- `Rate limit exceeded` - Wait a moment and retry
- `Request timed out` - Try again
- `Image too large` - Reduce image size to <5MB

Detailed errors are logged server-side for debugging.

## Troubleshooting

### Models not showing up
1. Verify the pipeline is imported correctly
2. Check Open WebUI logs for import errors
3. Restart Open WebUI if needed

### API key errors
1. Ensure your API key starts with `sk-ant-`
2. Check there are no extra spaces in the key
3. Verify the key is active in Anthropic Console

### Timeout errors
1. Check your internet connection
2. Verify Anthropic API status: [status.anthropic.com](https://status.anthropic.com/)
3. Try again in a moment

### Image upload issues
1. Ensure image is under 5MB
2. Supported formats: JPEG, PNG, GIF, WebP
3. For URL images, must be HTTPS

## Code Philosophy

This pipeline follows DHH's principles:

**Simple > Clever**
- ~340 lines of clean, readable code
- No unnecessary abstractions
- Clear intent over technical wizardry

**Secure by Default**
- Essential security features built-in
- No security theater (removed 60% of validation code from initial version)
- HTTPS-only, safe error handling

**Convention over Configuration**
- One configuration option (API key)
- Sensible defaults that work
- No feature flags for security

## Contributing

Contributions welcome! But remember:

**Before adding features, ask:**
1. Is this solving an actual problem or a theoretical one?
2. Can we solve this with less code?
3. Are we duplicating Anthropic's existing protections?

**Pull Request Guidelines:**
- Keep it simple
- Remove code when possible
- No security theater
- Test with real use cases

### How to Contribute
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test thoroughly
5. Commit (`git commit -m 'Add amazing feature'`)
6. Push (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Report Bugs
Open an issue with:
- What you tried
- What happened
- What you expected
- Relevant log excerpts

### Feature Requests
Remember: this project prioritizes simplicity. Feature requests that add unnecessary complexity may be declined.

## Resources

- [Anthropic API Documentation](https://docs.anthropic.com/)
- [Open WebUI Documentation](https://docs.openwebui.com/)
- [Claude Model Guide](https://docs.anthropic.com/en/docs/about-claude/models)
- [Anthropic Console](https://console.anthropic.com/)

---

**Remember:** This pipeline does everything you need and nothing you don't. If you find yourself wanting more configuration options, ask "why?" first.

Made with d for the Open WebUI community
