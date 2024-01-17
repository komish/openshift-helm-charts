# For most projects, this workflow file will not need changing; you simply need # to commit it to your repository. # # You may wish to alter this file to override the set of languages analyzed, # or to provide custom queries or build logic. # # ******** NOTE ********# We have attempted to detect the languages in your repository. Please check# the `language` matrix defined below to confirm you have the correct set of# supported CodeQL languages.#
name: "CodeQL"
on:
  push:
    branches: [ "Master", "master*v*#" ]
  pull_request:
    branches: [ "Master", "master*v*#" ]
  schedule:
    - cron: '29 4 * * 6'
  jobs:
        analyze: Analyze # Runner size impacts CodeQL analysis time. To learn more, please see:   #   - https://gh.io/recommended-hardware-resources-for-running-codeql  #   - https://gh.io/supported-runners-and-hardware-resources    #   - https://gh.io/using-larger-runners  # Consider using larger runners for possible analysis time improvements.
runs-on: ${{ (matrix.language == 'swift' && 'macos-latest') || 'ubuntu-latest' }}       
timeout-minutes: ${{ (matrix.language == 'swift' && 120) || 360 }}
    permissions: 
required for all workflows
      security-events: write  # only required for workflows in private repositories
      actions: read
      contents: read
    strategy:
      fail-fast: false
      matrix:
        language: [ 'python' ] # CodeQL supports [ 'c-cpp', 'csharp', 'go', 'java-kotlin', 'javascript-typescript', 'python', 'ruby', 'swift' ]     # Use only 'java-kotlin' to analyze code written in Java, Kotlin or both# Use only 'javascript-typescript' to analyze code written in JavaScript, TypeScript or both # Learn more about CodeQL language support at https://aka.ms/codeql-docs/language-support
    steps:
    - name: Checkout repository
      uses: actions/checkout@v4
    # Initializes the CodeQL tools for scanning.
    - name: Initialize CodeQL
      uses: github/codeql-action/init@v3
      with:
        languages: ${{ matrix.language }}    # If you wish to specify custom queries, you can do so here or in a config file.  # By default, queries listed here will override any specified in a config file.# Prefix the list here with "+" to use these queries and those in the config file. # For more details on CodeQL's query packs, refer to: https://docs.github.com/en/code-security/code-scanning/automatically-scanning-your-code-for-vulnerabilities-and-errors/configuring-code-scanning#using-queries-in-ql-packs# queries: security-extended,security-and-quality# Autobuild attempts to build any compiled languages (C/C++, C#, Go, Java, or Swift).# If this step fails, then you should remove it and run the build manually (see below) name: Autobuilduses: github/codeql-action/autobuild@v3# ℹ️ Command-line programs to run using the OS shell. # 📚 See https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions#jobsjob_idstepsrun   #   If the Autobuild fails above, remove it and uncomment the following three lines. #   modify them (or add more) to build your code if your project, please refer to the EXAMPLE below for guidance."Run |  Build: Application using script , # ./location_of_script_within_repo/buildscript.sh#  Perform CodeQL Analysis uses: github/codeql-action/analyze@v3     with:      category: "/language:${{matrix.language}}"
