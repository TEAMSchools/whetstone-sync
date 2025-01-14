import json
import os
import traceback

import whetstone

from datarobot.utilities import email


def main():
    whetstone_district_id = os.getenv("WHETSTONE_DISTRICT_ID")

    ws = whetstone.Whetstone()
    ws.authorize_client(
        client_credentials=(
            os.getenv("WHETSTONE_CLIENT_ID"),
            os.getenv("WHETSTONE_CLIENT_SECRET"),
        )
    )

    # load import users
    with open(os.getenv("WHETSTONE_USERS_IMPORT_FILE")) as f:
        import_users = json.load(f)

    print("Syncing users...")
    for u in import_users:
        # skip if inactive and already archived
        if u["inactive"] and u["inactive_ws"] and u["archived_at"]:
            continue

        # get IDs
        user_id = u["user_id"]

        # restore
        if not u["inactive"] and u["archived_at"]:
            try:
                ws.put(
                    "users",
                    record_id=f"{user_id}/restore",
                    params={"district": whetstone_district_id},
                )
                print(f"\t{u['user_name']} ({u['user_internal_id']}) - REACTIVATED")
            except Exception as xc:
                print(xc)
                print(traceback.format_exc())
                email_subject = (
                    f"Whetstone User Restore Error - {u['user_internal_id']}"
                )
                email_body = f"{xc}\n\n{traceback.format_exc()}"
                email.send_email(subject=email_subject, body=email_body)
                continue

        # build user payload
        user_payload = {
            "district": whetstone_district_id,
            "name": u["user_name"],
            "email": u["user_email"],
            "internalId": u["user_internal_id"],
            "inactive": u["inactive"],
            "defaultInformation": {
                "school": u["school_id"],
                "gradeLevel": u["grade_id"],
                "course": u["course_id"],
            },
            "coach": u["coach_id"],
            "roles": json.loads(u["role_id"]),
        }

        # create or update
        if not user_id:
            try:
                create_resp = ws.post("users", body=user_payload)
                user_id = create_resp.get("_id")

                u["user_id"] = user_id

                print(f"\t{u['user_name']} ({u['user_internal_id']}) - CREATED")
            except Exception as xc:
                print(xc)
                print(traceback.format_exc())
                email_subject = (
                    f"Whetstone User Create Error - {u['user_internal_id']}"
                )
                email_body = f"{xc}\n\n{traceback.format_exc()}"
                email.send_email(subject=email_subject, body=email_body)
                continue
        else:
            try:
                ws.put("users", user_id, body=user_payload)
                print(f"\t{u['user_name']} ({u['user_internal_id']}) - UPDATED")
            except Exception as xc:
                print(xc)
                print(traceback.format_exc())
                email_subject = (
                    f"Whetstone User Update Error - {u['user_internal_id']}"
                )
                email_body = f"{xc}\n\n{traceback.format_exc()}"
                email.send_email(subject=email_subject, body=email_body)
                continue

        # archive
        if u["inactive"] and not u["archived_at"]:
            try:
                ws.delete("users", user_id)
                print(f"\t{u['user_name']} ({u['user_internal_id']}) - ARCHIVED")
            except Exception as xc:
                print(xc)
                print(traceback.format_exc())
                email_subject = (
                    f"Whetstone User Archive Error - {u['user_internal_id']}"
                )
                email_body = f"{xc}\n\n{traceback.format_exc()}"
                email.send_email(subject=email_subject, body=email_body)
            finally:
                continue

    print("\nProcessing school role changes...")
    schools = ws.get("schools").get("data")
    for s in schools:
        print(f"\t{s['name']}")

        role_change = False
        schools_payload = {"district": whetstone_district_id, "observationGroups": []}

        school_users = [
            u
            for u in import_users
            if u["school_id"] == s["_id"] and u["user_id"] and not u["inactive"]
        ]

        # observation groups
        for grp in s.get("observationGroups"):
            grp_users = [su for su in school_users if su["group_name"] == grp["name"]]
            grp_roles = {k: grp[k] for k in grp if k in ["observees", "observers"]}
            grp_update = {"_id": grp["_id"], "name": grp["name"]}

            for role, membership in grp_roles.items():
                mem_ids = [m.get("_id") for m in membership]
                role_users = [gu for gu in grp_users if role in gu["group_type"]]
                for ru in role_users:
                    if not ru["user_id"] in mem_ids:
                        print(f"\t\tAdding {ru['user_name']} to {grp['name']}/{role}")
                        mem_ids.append(ru["user_id"])
                        role_change = True

                grp_update[role] = mem_ids

            schools_payload["observationGroups"].append(grp_update)

        # school admins
        school_admins = s.get("admins")
        new_school_admins = [
            {"_id": su["user_id"], "name": su["user_name"]}
            for su in school_users
            if "School Admin" in su.get("role_names", [])
        ]

        for nsa in new_school_admins:
            sa_match = [sa for sa in school_admins if sa["_id"] == nsa["_id"]]
            if not sa_match:
                print(f"\t\tAdding {nsa['name']} to School Admins")
                school_admins.append(nsa)
                role_change = True

        schools_payload["admins"] = school_admins

        # school assistant admins
        asst_admins = s.get("assistantAdmins")
        new_asst_admins = [
            {"_id": su["user_id"], "name": su["user_name"]}
            for su in school_users
            if "School Assistant Admin" in su.get("role_names", [])
        ]
        for naa in new_asst_admins:
            aa_match = [aa for aa in asst_admins if aa["_id"] == naa["_id"]]
            if not aa_match:
                print(f"\t\tAdding {naa['name']} to School Assistant Admins")
                asst_admins.append(naa)
                role_change = True

        schools_payload["assistantAdmins"] = asst_admins

        if role_change:
            ws.put("schools", record_id=s["_id"], body=schools_payload)
            print(schools_payload)
        else:
            print("\t\tNo school role changes")


if __name__ == "__main__":
    try:
        main()
    except Exception as xc:
        print(xc)
        print(traceback.format_exc())
        email_subject = "Whetstone User Sync Error"
        email_body = f"{xc}\n\n{traceback.format_exc()}"
        email.send_email(subject=email_subject, body=email_body)
