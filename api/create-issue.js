async function handler(req, res) {
  // CORS
  res.setHeader('Access-Control-Allow-Credentials', 'true');
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS,PATCH,DELETE,POST,PUT');
  res.setHeader('Access-Control-Allow-Headers', 'X-CSRF-Token,X-Requested-With,Accept,Accept-Version,Content-Length,Content-MD5,Content-Type,Date,X-Api-Version');

  // Handle OPTIONS
  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  // Only POST
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }

  try {
    const { url } = req.body;

    // Validate
    if (!url || !url.includes('instagram.com')) {
      res.status(400).json({ error: 'Invalid Instagram URL' });
      return;
    }

    const token = process.env.GITHUB_TOKEN;
    if (!token) {
      res.status(500).json({ error: 'GITHUB_TOKEN not configured' });
      return;
    }

    // Create issue
    const reelId = url.split('/').slice(-2, -1)[0] || 'reel';
    const issueRes = await fetch('https://api.github.com/repos/xopromo/telethon/issues', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
      },
      body: JSON.stringify({
        title: `Download Reel: ${reelId}`,
        body: `**Instagram URL:**\n${url}\n\n_Processed by GitHub Actions workflow._`,
        labels: ['reel-download']
      })
    });

    if (!issueRes.ok) {
      const errText = await issueRes.text();
      throw new Error(`GitHub API (${issueRes.status}): ${errText}`);
    }

    const issue = await issueRes.json();
    res.status(201).json({
      success: true,
      issue_url: issue.html_url,
      issue_number: issue.number
    });

  } catch (error) {
    console.error('Error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
}

export default handler;
