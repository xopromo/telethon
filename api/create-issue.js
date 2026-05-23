/**
 * Vercel Serverless Function
 * Creates GitHub Issue for reel download
 *
 * POST /api/create-issue
 * Body: { url: "https://www.instagram.com/p/..." }
 */

module.exports = async function handler(req, res) {
  // CORS headers
  res.setHeader('Access-Control-Allow-Credentials', 'true');
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS,PATCH,DELETE,POST,PUT');
  res.setHeader('Access-Control-Allow-Headers', 'X-CSRF-Token,X-Requested-With,Accept,Accept-Version,Content-Length,Content-MD5,Content-Type,Date,X-Api-Version');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  // Only allow POST
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { url } = req.body;

  // Validate URL
  if (!url || !url.includes('instagram.com')) {
    return res.status(400).json({ error: 'Invalid Instagram URL' });
  }

  // Check if token exists
  const token = process.env.GITHUB_TOKEN;
  if (!token) {
    return res.status(500).json({ error: 'GitHub token not configured' });
  }

  try {
    // Extract reel ID for title
    const reelId = url.split('/').slice(-2, -1)[0] || 'reel';

    // Create GitHub Issue
    const response = await fetch(
      'https://api.github.com/repos/xopromo/telethon/issues',
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Accept': 'application/vnd.github+json',
          'X-GitHub-Api-Version': '2022-11-28',
        },
        body: JSON.stringify({
          title: `Download Reel: ${reelId}`,
          body: `**Instagram URL:**\n${url}\n\n_This issue will be processed automatically by the workflow._`,
          labels: ['reel-download']
        })
      }
    );

    if (!response.ok) {
      const error = await response.json();
      console.error('GitHub API error:', error);
      throw new Error(`GitHub API error: ${response.statusText}`);
    }

    const issue = await response.json();

    // Success response
    return res.status(201).json({
      success: true,
      issue_url: issue.html_url,
      issue_number: issue.number,
      message: '✅ Issue created! GitHub Actions will process it now.'
    });

  } catch (error) {
    console.error('Error:', error);
    return res.status(500).json({
      success: false,
      error: error.message || 'Failed to create issue'
    });
  }
}
