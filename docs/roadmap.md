# Anchor Development Roadmap

## Current Technical Debt

### API Structure
**Issue**: Webhook endpoints using simplified URL structure
- Current: `/webhook` for all SMS handling
- Target: `/sms/webhook` with proper API namespacing
**Priority**: Low
**Effort**: Medium
**Dependencies**: None
**Reasoning**:
1. Better API organization and namespacing
2. Clearer endpoint purpose
3. Allows for future expansion (e.g., `/email/webhook`, `/voice/webhook`)
4. Follows RESTful conventions

**Action Items**:
- [ ] Update Flask blueprint to use `url_prefix='/sms'`
- [ ] Update Twilio webhook URL configuration
- [ ] Update tests and documentation
- [ ] Add integration tests for webhook routing

## Planned Features
1. User Timezone Management
2. Task Scheduling and Calendar Integration
3. Daily Planning and Reflection Workflows
4. Quick Start Onboarding Flow
   - User timezone capture
   - Welcome tutorial
   - First-time user experience
   - Automated setup guidance
   **Priority**: Medium
   **Dependencies**: Core planning workflow
   **Reasoning**: Improve user onboarding experience after core functionality is stable

## Completed Items
- [x] Initial SMS webhook implementation
- [x] Basic message handling structure
- [x] Twilio integration
- [x] Calendar link generation service
- [x] Google Gemini Integration
  - [x] Structured response parsing with Pydantic
  - [x] Conversation context management
  - [x] Error handling and recovery
  - [x] Natural language task extraction

## Future Improvements
- [ ] Enhanced LLM prompting for better task extraction
- [ ] Improved error recovery strategies
- [ ] More sophisticated context management
- [ ] Better timing extraction for complex schedules
- [ ] Evaluate Gemini function calling when available
  - Current marker-based parsing is stable but basic
  - Function calling could provide better structure
  - Wait for mature Gemini support before implementing