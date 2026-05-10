# GitHub Repository Setup Instructions

## Step 1: Create GitHub Repository
1. Go to https://github.com and sign in to your account
2. Click the "+" button in the top right corner
3. Select "New repository"
4. Fill in repository details:
   - **Repository name**: `patent-intelligence-pipeline`
   - **Description**: `Global Patent Intelligence Data Pipeline - Complete data engineering pipeline for USPTO patent analysis`
   - **Visibility**: Choose "Public" (for course submission) or "Private"
   - **DO NOT** initialize with README, .gitignore, or license (we already have these)

## Step 2: Connect Local Repository to GitHub
After creating the repository on GitHub, GitHub will show you quick setup options. Choose "...or push an existing repository from the command line" and run these commands:

```bash
git remote add origin https://github.com/YOUR_USERNAME/patent-intelligence-pipeline.git
git branch -M main
git push -u origin main
```

Replace `YOUR_USERNAME` with your actual GitHub username.

## Step 3: Verify Repository
1. Visit your GitHub repository page
2. Verify all files are uploaded:
   - README.md
   - requirements.txt
   - main.py
   - scripts/ folder with all Python files
   - LICENSE
   - CONTRIBUTING.md
   - .gitignore

## Step 4: Repository Settings (Optional)
1. Go to repository Settings
2. Enable "Issues" for bug tracking
3. Enable "Wikis" if you want additional documentation
4. Set up branch protection rules if needed

## Step 5: Share with Course Instructor
Once everything is uploaded, share the repository URL with your course instructor for submission.

## Repository URL Format
Your repository will be available at:
`https://github.com/YOUR_USERNAME/patent-intelligence-pipeline`

## Next Steps
After setting up GitHub:
1. Test the pipeline one more time: `python main.py`
2. Consider adding real USPTO data
3. Document any specific customizations you made
4. Prepare submission documentation

---

**Note**: Make sure you have Git installed and configured with your name and email:
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```
