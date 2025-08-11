"""Reusable HTML templates for proposals and related UI."""

# Export Proposal HTML template
# Note: Keep as a plain triple-quoted string (not an f-string) so double-curly
# braces like {{placeholder}} are preserved as-is for client-side rendering.
EXPORT_PROPOSAL_HTML_TEMPLATE: str = """<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>Export Proposal</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        h1 { text-align: center; }
        .section { margin-bottom: 20px; }
        .contact-info p { margin: 2px 0; }
    </style>
    <script>
        // Optional hint for clients that parse the template directly
        // They may also rely on the API JSON field `generateProposal: true`
        var response = { generateProposal: true };
    </script>
</head>
<body>
    <h1>Export Proposal</h1>

    <div class=\"section\">
        <p><strong>Exporter:</strong> {{exporter_name}}</p>
        <p><strong>Consignee:</strong> {{consignee_name}}</p>
        <p><strong>Destination Country:</strong> {{destination_country}}</p>
        <p><strong>Date:</strong> {{proposal_date}}</p>
    </div>

    <div class=\"section\">
        <h2>Product Summary</h2>
        <p>{{generated_product_summary}}</p>
    </div>

    <div class=\"section\">
        <h2>Key Advantages</h2>
        <p>{{generated_product_advantages}}</p>
    </div>

    <div class=\"section\">
        <h2>Pricing & Stock Availability</h2>
        <p>{{generated_pricing_stock}}</p>
    </div>

    <div class=\"section\">
        <h2>Our Competitive Edge</h2>
        <p>{{generated_exporter_edge}}</p>
    </div>

    <div class=\"section\">
        <h2>Call to Action</h2>
        <p>{{generated_call_to_action}}</p>
    </div>

    <div class=\"section contact-info\">
        <h2>Contact Information</h2>
        <p><strong>Email:</strong> {{contact_email}}</p>
        <p><strong>Phone:</strong> {{contact_phone}}</p>
        <p><strong>Website:</strong> {{contact_website}}</p>
    </div>
</body>
</html>
"""


