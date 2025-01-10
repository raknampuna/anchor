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
1. Google Gemini Integration for Natural Language Processing
   - Using Gemini API for message understanding and generation
   - Implement conversation context management
2. User Timezone Management
3. Task Scheduling and Calendar Integration
4. Daily Planning and Reflection Workflows
5. Quick Start Onboarding Flow
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