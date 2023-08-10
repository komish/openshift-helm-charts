import re
import os
import sys
import argparse
import json

import requests
import semver
import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

sys.path.append('../')
from owners import owners_file
from report import verifier_report
from pullrequest import prartifact
from tools import gitutils

ALLOW_CI_CHANGES = "allow/ci-changes"
TYPE_MATCH_EXPRESSION = "(partners|redhat|community)"

def check_web_catalog_only(report_in_pr, num_files_in_pr, report_file_match):

    print(f"[INFO] report in PR {report_in_pr}")
    print(f"[INFO] num files in PR {num_files_in_pr}")
    
    category, organization, chart, version = report_file_match.groups()

    print(f"read owners file : {category}/{organization}/{chart}" )
    found_owners,owner_data = owners_file.get_owner_data(category, organization, chart)

    if found_owners:
        owner_web_catalog_only = owners_file.get_web_catalog_only(owner_data)
        print(f"[INFO] webCatalogOnly/providerDelivery from OWNERS : {owner_web_catalog_only}")
    else:
        msg = "[ERROR] OWNERS file was not found."
        print(msg)
        gitutils.add_output("owners-error-message",msg)
        sys.exit(1)

    if report_in_pr:
        report_file_path = os.path.join("pr-branch","charts", category, organization, chart, version, "report.yaml")
        print(f"read report file : {report_file_path}" )
        found_report,report_data = verifier_report.get_report_data(report_file_path)

        if found_report:
            report_web_catalog_only = verifier_report.get_web_catalog_only(report_data)
            print(f"[INFO] webCatalogOnly/providerDelivery from report : {report_web_catalog_only}")
        else:
            msg = f"[ERROR] Failed tp open report: {report_file_path}."
            print(msg)
            gitutils.add_output("pr-content-error-message",msg)
            sys.exit(1)

    web_catalog_only = False
    if report_in_pr and num_files_in_pr > 1:
        if report_web_catalog_only or owner_web_catalog_only:
            msg = f"[ERROR] The web catalog distribution method requires the pull request to be report only."
            print(msg)
            gitutils.add_output("pr-content-error-message",msg)
            sys.exit(1)
    elif report_in_pr:
        if report_web_catalog_only and owner_web_catalog_only:
            if verifier_report.get_package_digest(report_data):
                web_catalog_only = True
            else:
                msg = f"[ERROR] The web catalog distribution method requires a package digest in the report."
                print(msg)
                gitutils.add_output("pr-content-error-message",msg)
                sys.exit(1)
        elif report_web_catalog_only:
            msg = f"[ERROR] Report indicates web catalog only but the distribution method set for the chart is not web catalog only."
            print(msg)
            gitutils.add_output("pr-content-error-message",msg)
            sys.exit(1)
        elif owner_web_catalog_only:
            msg = f"[ERROR] The web catalog distribution method is set for the chart but is not set in the report."
            print(msg)
            gitutils.add_output("pr-content-error-message",msg)
            sys.exit(1)

    if web_catalog_only:
        print(f"[INFO] webCatalogOnly/providerDelivery is a go")
        gitutils.add_output("webCatalogOnly","True")
    else:
        gitutils.add_output("webCatalogOnly","False")
        print(f"[INFO] webCatalogOnly/providerDelivery is a no-go")

def get_file_match_compiled_patterns():
    """Return a tuple of patterns, where the first can be used to match any file in a chart PR 
    and the second can be used to match a valid report file within a chart PR. The patterns
    match based on the relative path of a file to the base repository
    
    Both patterns capture chart type, chart vendor, chart name and chart version from the file path..
    
    Examples of valid file paths are:
    
    charts/partners/hashicorp/vault/0.20.0/<file>
    charts/partners/hashicorp/vault/0.20.0//report.yaml
    """

    pattern = re.compile(r"charts/"+TYPE_MATCH_EXPRESSION+"/([\w-]+)/([\w-]+)/([\w\.-]+)/.*")
    reportpattern = re.compile(r"charts/"+TYPE_MATCH_EXPRESSION+"/([\w-]+)/([\w-]+)/([\w\.-]+)/report.yaml")
    tarballpattern = re.compile(r"charts/(partners|redhat|community)/([\w-]+)/([\w-]+)/([\w\.-]+)/(.*\.tgz$)")
    return pattern,reportpattern,tarballpattern


def ensure_only_chart_is_modified(api_url, repository, branch):
    """Ensures that the pull request only modifies the appropriate files.

    Examples of what may cause failures are:
    - modifying multiple charts in a single PR
    - creating an OWNERs file and submitting your chart in the same PR
    - an existing release/tag for your chart in our repository.
    - an existing entry in our index for your chart.

    IF a failing case is found, this function will throw an error and write an
    accompanying message that will be sent to the PR to inform the submitter of
    issues they may need to resolve. This error is accompanied with a non-zero
    exit code.
    
    Args:
        api_url (String): the GitHub pull request URL. (E.g.https://api.github.com/repos/openshift-helm-charts/charts/pulls/1)
        repository (String): The org/repository (E.g. openshift-helm-charts/charts)
        branch (String): The branch in this repository that contains the Helm index to parse. (E.g. gh-pages)
    """
    # NOTE(KOMISH): DEBUG ADDITION
    print(f"[TRACE] api_url={api_url}")
    print(f"[TRACE] repository={repository}")
    print(f"[TRACE] branch={branch}")
    # /NOTE(KOMISH): DEBUG ADDITION
    label_names = prartifact.get_labels(api_url)
    for label_name in label_names:
        if label_name == ALLOW_CI_CHANGES:
            return

    # Parse modified files and look for anomalies.
    files = prartifact.get_modified_files(api_url)
    pattern,reportpattern,tarballpattern = get_file_match_compiled_patterns()
    matches_found = 0
    report_found = False
    none_chart_files = {}

    for file_path in files:
        match = pattern.match(file_path)
        if not match:
            file_name = os.path.basename(file_path)
            none_chart_files[file_name] = file_path
        else:
            matches_found += 1
            if reportpattern.match(file_path):
                print(f"[INFO] Report found: {file_path}")
                gitutils.add_output("report-exists","true")
                report_found = True
            else:
                tar_match = tarballpattern.match(file_path)
                if tar_match:
                    print(f"[INFO] tarball found: {file_path}")
                    _,_,chart_name,chart_version,tar_name = tar_match.groups()
                    expected_tar_name = f"{chart_name}-{chart_version}.tgz"
                    if tar_name != expected_tar_name:
                        msg = f"[ERROR] the tgz file is named incorrectly. Expected: {expected_tar_name}"
                        print(msg)
                        gitutils.add_output("pr-content-error-message",msg)
                        exit(1)

            if matches_found == 1:
                pattern_match = match
            elif pattern_match.groups() != match.groups():
                msg = "[ERROR] A PR must contain only one chart. Current PR includes files for multiple charts."
                print(msg)
                gitutils.add_output("pr-content-error-message",msg)
                exit(1)
    
    if none_chart_files:
        if len(files) > 1 or "OWNERS" not in none_chart_files: #OWNERS not present or preset but not the only file
            example_file = list(none_chart_files.values())[0]
            msg = f"[ERROR] PR includes one or more files not related to charts, e.g., {example_file}"
            print(msg)
            gitutils.add_output("pr-content-error-message",msg)

        if "OWNERS" in none_chart_files:
            file_path = none_chart_files["OWNERS"]
            path_parts = file_path.split("/")
            category = path_parts[1] # Second after charts
            if category == "partners":
                msg = "[ERROR] OWNERS file should never be set directly by partners. See certification docs."
                print(msg)
                gitutils.add_output("owners-error-message",msg)
            elif matches_found>0: # There is a mix of chart and non-chart files including OWNERS
                msg = "[ERROR] Send OWNERS file by itself in a separate PR."
                print(msg)
                gitutils.add_output("owners-error-message",msg)
            elif len(files) == 1: # OWNERS file is the only file in PR
                msg = "[INFO] OWNERS file changes require manual review by maintainers."
                print(msg)
                gitutils.add_output("owners-error-message",msg)
                
        sys.exit(1)

    check_web_catalog_only(report_found, matches_found, pattern_match)

    if matches_found>0:
        category, organization, chart, version = pattern_match.groups()
        gitutils.add_output("category",f"{'partner' if category == 'partners' else category}")
        gitutils.add_output("organization",organization)

        if not semver.VersionInfo.isvalid(version):
            msg = f"[ERROR] Helm chart version is not a valid semantic version: {version}"
            print(msg)
            gitutils.add_output("pr-content-error-message",msg)
            sys.exit(1)

        # Pull the index and make sure that no existing entry at the specified version exist.
        print("Downloading index.yaml", category, organization, chart, version)
        r = requests.get(f'https://raw.githubusercontent.com/{repository}/{branch}/index.yaml')

        if r.status_code == 200:
            data = yaml.load(r.text, Loader=Loader)
        else:
            data = {"apiVersion": "v1",
                "entries": {}}

        # Check existing entries to ensure that this release doesn't already exist, and that its
        # owned by this category-organization-chart
        entry_name = f"{organization}-{chart}"
        d = data["entries"].get(entry_name, [])
        # Note(komish): Also check for the new entry style where only the chart is added.
        d += data["entries"].get(chart, [])
        # gitutils.add_output("chart-entry-name",entry_name)
        gitutils.add_output("chart-entry-name",chart) # TODO(komish): See what happens if we just pull the org out of this value.
        for v in d:
            if v["version"] == version:
                msg = f"[ERROR] Helm chart release already exists in the index.yaml: {version}"
                print(msg)
                gitutils.add_output("pr-content-error-message",msg)
                sys.exit(1)
            
            # TODO(komish): This is a PoC checking if an annotation would be the right approach to establishing ownership.
            ownershipAnnotation = v["annotations"].get("charts.openshift.io/unique-identifier", "unknown")
            if ownershipAnnotation != f"{category}-{organization}-{chart}":
                msg = f"[ERROR] This chart does not appear to be owned by this submitter, and chart names must be globally unique."
                print(msg)
                gitutils.add_output("pr-content-error-message",msg)
                if ownershipAnnotation == "unknown":
                    print("[DEBUG] This chart's ownership annotation is missing! Maintainers must manual resolve this issue.")
                sys.exit(2)

        # Check the repository's tags to make sure a tag doesn't already exist
        # for this chart, as we'll need to create one if we need to publish this
        # chart.
        tag_name = f"{organization}-{chart}-{version}"
        gitutils.add_output("chart-name-with-version",tag_name)
        tag_api = f"https://api.github.com/repos/{repository}/git/ref/tags/{tag_name}"
        headers = {'Accept': 'application/vnd.github.v3+json','Authorization': f'Bearer {os.environ.get("BOT_TOKEN")}'}
        print(f"[INFO] checking tag: {tag_api}")
        r = requests.head(tag_api, headers=headers)
        if r.status_code == 200:
            msg = f"[ERROR] Helm chart release already exists in the GitHub Release/Tag: {tag_name}"
            print(msg)
            gitutils.add_output("pr-content-error-message",msg)
            sys.exit(1)
        try:
            if prartifact.xRateLimit in r.headers:
                print(f'[DEBUG] {prartifact.xRateLimit} : {r.headers[prartifact.xRateLimit]}')
            if prartifact.xRateRemain in r.headers:
                print(f'[DEBUG] {prartifact.xRateRemain}  : {r.headers[prartifact.xRateRemain]}')

            response_content = r.json()
            if "message" in response_content:
                print(f'[ERROR] getting index file content: {response_content["message"]}')
                sys.exit(1)
        except json.decoder.JSONDecodeError:
            pass




def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--index-branch", dest="branch", type=str, required=True,
                                        help="index branch")
    parser.add_argument("-r", "--repository", dest="repository", type=str, required=True,
                                        help="Git Repository")
    parser.add_argument("-u", "--api-url", dest="api_url", type=str, required=True,
                                        help="API URL for the pull request")
    args = parser.parse_args()
    branch = args.branch.split("/")[-1]
    ensure_only_chart_is_modified(args.api_url, args.repository, branch)


if __name__ == "__main__":
    main()
