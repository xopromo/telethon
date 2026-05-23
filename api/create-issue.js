export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { url } = req.body;

  if (!url || !url.includes('instagram.com')) {
    return res.status(400).json({ error: 'Invalid Instagram URL' });
  }

  const token = process.env.GITHUB_TOKEN;
  if (!token) {
    return res.status(500).json({ error: 'GitHub token not configured' });
  }

  try {
    const reelId = url.split('/').slice(-2, -1)[0] || 'reel';

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
      throw new Error(`GitHub API error: ${response.statusText}`);
    }

    const issue = await response.json();

    return res.status(201).json({
      success: true,
      issue_url: issue.html_url,
      issue_number: issue.number,
      message: '✅ Issue created! GitHub Actions will process it now.'
    });

  } catch (error) {
    return res.status(500).json({
      success: false,
      error: error.message || 'Failed to create issue'
    });
  }
}
