# TaskFlow Section 6 - Functionality Testing

Test date: 2-3 September 2026 (Pacific/Auckland)  
Implementation tested: `backend/` Flask application  
Automated result: **42 passed, 1 dependency deprecation warning**  
Assessment test-case result: **24 PASS, 0 FAIL, 0 PASS AFTER FIX, 0 NOT TESTED**

## Verified implementation scope

Repository inspection confirmed that the current application implements registration, login/logout, profile and password management, user-owned task CRUD, completion/reopening, soft-drop, scheduled/due-date validation, four stored task statuses (`yet-to-do`, `on-going`, `completed`, and `dropped`), three priorities, title-substring search, status/priority/due-date filters, dashboard calculations, calculated overdue presentation, Task History, remarks, reflection/lessons learned, notification categories, and responsive layouts. Overdue is calculated from dates and is not stored as a status. Search is implemented against task titles; description-wide keyword search is not implemented.

The assessment DOCX was used only as requirements context. Results below are based on the repository and executed tests, not on claims in that document.

## 6.a Testing Strategy

Black-box functional testing was used to compare observable application behaviour with the expected result for each assessment test case. Routes were exercised through Flask's test client using realistic form submissions, redirects, rendered responses, authentication sessions, and database queries used only to verify persisted outcomes. Each pytest test received a new temporary SQLite database through the existing `tmp_path` fixture, replacing the normal PostgreSQL connection and preventing any access to the production database or AWS resources.

Browser testing used the existing rendered Flask/Jinja2 interface running locally on a separate SQLite database. The browser workflow exercised login, task creation, validation feedback, completion, filtering, dashboard output, Task History, stored remarks/reflection, notifications, and responsive viewports. Screenshots were captured from actual rendered states. Desktop (1440 px), tablet (768 px), mobile (375 px), and a mobile task modal were checked visually; measured document widths showed no major horizontal overflow.

The original 35-test suite was run unchanged first and passed. Additional assessment-only tests were then added for uncovered cases. No application code or UI was changed.

## 6.b Black-box Test Cases

| Test ID | Function | Test Action | Expected Result | Actual Result | Status | Evidence |
|---|---|---|---|---|---|---|
| TC-01 | Valid Registration | Submitted a valid name, unique email, and matching password/confirmation. | Account is successfully created. | Response displayed the account-created message; a new user row existed and its password hash authenticated the supplied password. | PASS | `tests/test_assessment_functionality.py::test_tc01_valid_registration_creates_account`; final pytest run |
| TC-02 | Duplicate Email Registration | Submitted registration using an existing user's email. | Registration is rejected with an appropriate message. | Response displayed `An account with that email already exists.` and the database retained one matching user. | PASS | `tests/test_auth.py::test_duplicate_registration_is_rejected`; final pytest run |
| TC-03 | Valid Login | Submitted a registered email and correct password. | User logs in successfully. | Login redirected to the dashboard, displayed `Welcome back!`, and rendered authenticated dashboard content. | PASS | `tests/test_assessment_functionality.py::test_tc03_valid_login_starts_authenticated_session`; `testing_evidence/TC03_login_pass.png` |
| TC-04 | Invalid Login | Submitted a correct email with an incorrect password. | Login is rejected and an error message is shown. | Login remained unauthenticated and displayed `Incorrect email or password.` | PASS | `tests/test_auth.py::test_invalid_login_is_rejected`; final pytest run |
| TC-05 | Logout | Logged out from an authenticated session, then requested the dashboard. | Session ends and protected pages require authentication again. | Logout redirected to login; the subsequent dashboard request also redirected to login. | PASS | `tests/test_auth.py::test_successful_logout`; final pytest run |
| TC-06 | Create Valid Task | Submitted title, description, scheduled date, due date, and high priority through the route and browser modal. | Task is saved and displayed. | Task was committed with the correct owner, dates, priority, and active status; browser showed `Task created successfully.` and the new card. | PASS | `tests/test_task_core.py::test_create_task`; `testing_evidence/TC06_create_task_pass.png` |
| TC-07 | Past Scheduled Date Validation | Submitted a scheduled date one day earlier than the current NZ date. | Task is rejected. | Request returned HTTP 400, no task was saved, and the modal displayed `Scheduled date cannot be in the past.` | PASS | `tests/test_task_validation.py::test_create_task_rejects_past_scheduled_date`; `testing_evidence/TC07_past_date_validation.png` |
| TC-08 | Scheduled Date After Due Date | Submitted a scheduled date later than the due date. | Task is rejected. | Request returned HTTP 400, no task was saved, and the modal displayed `Scheduled date cannot be after the due date.` | PASS | `tests/test_task_validation.py::test_create_task_rejects_schedule_after_due_date`; `testing_evidence/TC08_date_range_validation.png` |
| TC-09 | Edit Task | Changed an existing task's title, description, priority, and dates. | Updated values are saved. | All submitted values persisted and the active status remained consistent with the scheduled date. | PASS | `tests/test_task_additional.py::test_edit_task_persists_changes`; final pytest run |
| TC-10 | Complete Task | Posted the completion toggle for an active task and also completed it through the rendered control. | Status changes and `completed_at` is populated. | Stored status became `completed`, `completed_at` was non-null, and the browser card/dashboard showed Finished. | PASS | `tests/test_task_core.py::test_complete_task`; `testing_evidence/TC10_complete_task.png` |
| TC-11 | Reopen Task | Toggled a completed future task back to incomplete and reviewed a historical completed task as on-going. | Task becomes active and `completed_at` is cleared. | Future task returned to `yet-to-do`; past task returned to `on-going`; both cleared `completed_at`. | PASS | `tests/test_task_additional.py::test_finished_future_task_can_return_to_incomplete`; `tests/test_task_history_review.py::test_review_finished_task_back_to_ongoing` |
| TC-12 | Drop Task | Posted the drop action for an active task. | Status becomes Dropped without permanently deleting its history. | Row remained present and its stored status became `dropped`; dropped tasks could not subsequently be completed. | PASS | `tests/test_task_core.py::test_drop_task`; `tests/test_task_additional.py::test_dropped_task_cannot_be_completed` |
| TC-13 | Search Tasks | Searched the Task List by a distinctive title substring. | Matching tasks are returned. | Matching task card was rendered and the non-matching task card was absent. Current implementation searches title text only. | PASS | `tests/test_task_core.py::test_search_tasks`; final pytest run |
| TC-14 | Filter Tasks | Applied each status, each priority, a due date, and a combined high/medium priority filter; browser also applied on-going + high. | Only matching tasks are shown. | Every filter returned the expected task cards and excluded non-matching cards. | PASS | `tests/test_dashboard_filters.py`; `tests/test_task_additional.py::test_multiple_priority_filters_work_together`; `testing_evidence/TC14_filters.png` |
| TC-15 | Overdue Calculation | Created an unfinished task with a past due date and viewed the dashboard. | It is identified as overdue without changing stored status to `overdue`. | Dashboard displayed the Overdue indicator and count while the database status remained `on-going`. | PASS | `tests/test_dashboard_filters.py::test_overdue_task_stays_active`; `testing_evidence/TC15_overdue.png` |
| TC-16 | Dashboard Calculations | Used on-going, completed, dropped, and overdue tasks and inspected counts/progress. | Totals, pending/overdue counts, and daily progress are correct. | Executed case produced correct category counts, excluded dropped tasks from progress, and calculated 1 of 2 (50%); browser evidence independently showed a correct 1 of 3 (33%) state. | PASS | `tests/test_dashboard_filters.py::test_dashboard_counts_and_progress`; `testing_evidence/TC16_dashboard.png` |
| TC-17 | Task History | Queried history containing a prior-day completed task and a prior-day dropped task. | Appropriate completed/dropped tasks appear in Task History. | Both completed and dropped historical records were returned; active carry-over tasks were excluded. | PASS | `tests/test_task_history_review.py`; `tests/test_assessment_functionality.py::test_tc17_past_dropped_task_appears_in_history`; `testing_evidence/TC17_task_history.png` |
| TC-18 | Remarks and Reflection | Submitted remarks and reflection for a historical task, then rendered its details. | Information is stored and displayed correctly. | Both fields persisted exactly and were displayed in the task details modal. | PASS | `tests/test_task_history_review.py::test_review_saves_remarks_and_reflection`; `testing_evidence/TC18_reflection.png` |
| TC-19 | Notifications | Created unfinished overdue, due-today, and upcoming tasks. | Correct notification category is generated. | Notification context/render produced one Overdue, one Today, and one Upcoming item with correct dates and a total of three reminders. | PASS | `tests/test_assessment_functionality.py::test_tc19_notification_categories_are_generated`; `testing_evidence/TC19_notifications.png` |
| TC-20 | User-Specific Access Control | Authenticated as User B and attempted to view, edit, complete, drop, and review User A's task. | Access is denied or the task cannot be retrieved. | User A's card was absent from User B's list and all mutation attempts returned HTTP 404 without changing the task. | PASS | `tests/test_task_security.py` (five ownership/security tests); final pytest run |
| TC-21 | Profile Update | Submitted a valid new name and email. | New information is saved. | Success message was returned and both fields persisted on the authenticated user. | PASS | `tests/test_assessment_functionality.py::test_tc21_profile_update_persists`; final pytest run |
| TC-22 | Password Update | Changed the password, logged out, then tried the old and new passwords. | Old password no longer authenticates and new password works. | Old password produced the invalid-login message; new password logged in successfully. | PASS | `tests/test_assessment_functionality.py::test_tc22_password_update_invalidates_old_password`; final pytest run |
| TC-23 | Data Persistence | Created a task, logged out, logged back in, and requested the Task List. | Task remains stored and available. | The task was still in the database and rendered after a new authenticated session. | PASS | `tests/test_assessment_functionality.py::test_tc23_task_persists_across_logout_and_login`; final pytest run |
| TC-24 | Responsive Interface | Rendered dashboard at 1440x900, 768x1024, and 375x812; opened create modal at 375x812; inspected screenshots and measured document width. | Navigation, forms, task cards, modals, and controls remain readable/usable without major horizontal overflow. | Desktop/tablet layouts remained clear; mobile navigation collapsed appropriately; cards and modal controls remained readable. Overflow checks were false at all three widths and for the mobile modal. | PASS | `testing_evidence/TC24_desktop.png`; `testing_evidence/TC24_tablet.png`; `testing_evidence/TC24_mobile.png`; `testing_evidence/TC24_mobile_modal.png` |

## 6.c Test Results

- Assessment test cases executed: **24**
- Passed: **24**
- Failed: **0**
- Passed after fixes: **0**
- Not tested: **0**
- Repeatable pytest checks in the final run: **42 passed** in 88.66 seconds

No functional failure was found, so no application fix was proposed or applied. The first pytest command could not use the sandbox-restricted Windows temporary directory; rerunning with `--basetemp` inside the workspace allowed the tests to execute and is not an application defect. The only final-run warning was a Flask-Login dependency deprecation warning concerning `datetime.utcnow()`; it did not affect behaviour or test results.

One implementation boundary should be stated accurately: Task List search currently matches task titles through a case-insensitive substring query. It does not search descriptions, remarks, or reflections.

## 6.d Test Evidence

- `testing_evidence/TC03_login_pass.png` - authenticated dashboard after valid login.
- `testing_evidence/TC06_create_task_pass.png` - success message and newly rendered task card.
- `testing_evidence/TC07_past_date_validation.png` - rejected past scheduled date and visible validation message.
- `testing_evidence/TC08_date_range_validation.png` - rejected scheduled-date-after-due-date combination.
- `testing_evidence/TC10_complete_task.png` - completed task shown as Finished with updated dashboard counts.
- `testing_evidence/TC14_filters.png` - selected on-going and high filters with only the matching task displayed.
- `testing_evidence/TC15_overdue.png` - overdue task indicator and dashboard overdue count.
- `testing_evidence/TC16_dashboard.png` - summary totals, pending/overdue counts, and 33% daily progress.
- `testing_evidence/TC17_task_history.png` - completed historical task displayed in Task History.
- `testing_evidence/TC18_reflection.png` - task details displaying saved Remarks and Reflection & Lessons Learned.
- `testing_evidence/TC19_notifications.png` - overdue, today, and upcoming notification categories.
- `testing_evidence/TC24_desktop.png` - dashboard at 1440 px.
- `testing_evidence/TC24_tablet.png` - dashboard at 768 px.
- `testing_evidence/TC24_mobile.png` - dashboard/task cards at 375 px.
- `testing_evidence/TC24_mobile_modal.png` - readable create-task form and controls at 375 px.

Automated evidence is contained in `backend/tests/`. The final reproducible command was:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q --basetemp '.test_tmp_final' -p no:cacheprovider
```

## Manual follow-up still recommended

The 24 requested cases were executed locally, but the following checks remain useful before submission because they depend on the real deployment environment rather than application logic alone:

1. Repeat a non-destructive smoke test on the deployed AWS URL using a dedicated assessment account.
2. Confirm persistence through the deployed PostgreSQL/RDS connection after an application restart or redeployment.
3. Check the responsive pages on at least one physical phone and one tablet, including touch operation of the navigation, date controls, and modals.
4. Confirm current production browser compatibility in Chrome, Edge, and Firefox without using or exposing real credentials in evidence.
