# Epic 7: Frontend Modernization (Week 8)

**Epic Goal:** Modernize the frontend architecture by replacing Gradio with Vue 3 + FastAPI, providing better maintainability, performance, and scalability while preserving all existing UI functionality.

**Epic Value:** Establishes a sustainable, modern frontend architecture that decouples UI from backend logic, enables real-time updates via WebSocket, and provides a foundation for future UI enhancements.

**Timeline:** Week 8

**Deliverable:** Production-ready Vue 3 frontend with full feature parity to Epic 5 Gradio UI

---

## Background & Context

### Why This Epic?

Epic 5 successfully delivered a functional Gradio-based UI that provides monitoring and control capabilities. However, as the system evolves, we've identified architectural limitations:

1. **Tight Coupling:** Gradio UI is embedded in the Python backend, making independent scaling and deployment difficult
2. **Limited Customization:** Gradio's component-based approach restricts UI/UX flexibility
3. **Maintenance Concerns:** Mixing Python UI code with backend logic reduces code clarity
4. **Modern Standards:** Industry-standard frontend frameworks (Vue, React) provide better tooling, testing, and developer experience
5. **Real-time Performance:** Native WebSocket support in Vue provides better real-time update performance than Gradio's polling

### Strategic Direction

This epic represents a **strategic architectural improvement** rather than new feature development. It maintains 100% feature parity with Epic 5 while establishing:

- **Separation of Concerns:** Frontend and backend as independent services
- **Modern Tech Stack:** Vue 3, Vite, Pinia for frontend state management
- **Real-time Architecture:** WebSocket-first design for live updates
- **Scalability:** Independent deployment and scaling of frontend/backend
- **Developer Experience:** Hot Module Replacement (HMR), component-based development, modern tooling

### Success Criteria

✅ **Feature Parity:** All Epic 5 functionality preserved (Dashboard, Pipeline View, Pending Jobs, Approval Mode, Dry-Run Mode)
✅ **Performance:** Real-time updates via WebSocket (no polling delays)
✅ **Maintainability:** Clear separation between frontend and backend code
✅ **Zero Downtime:** Gradio UI remains functional until Vue 3 UI is production-ready
✅ **Developer Velocity:** Hot reload, component reusability, modern debugging tools

---

## Stories

### Story 7.1: Vue 3 Frontend Migration ✅

**As a** system maintainer,
**I want to** replace the Gradio UI with a modern Vue 3 + FastAPI frontend architecture,
**so that** the system has a more maintainable, performant, and flexible UI with better real-time capabilities.

**Status:** Draft

**Scope:**
- Add WebSocket support to FastAPI backend
- Create Vue 3 frontend project with Vite
- Implement all UI components (Dashboard, JobTable, PipelineView, PendingJobs)
- Setup Pinia state management with API/WebSocket integration
- Update Docker configuration for frontend service
- Remove Gradio completely
- Comprehensive testing and documentation

**Deliverables:**
- Functional Vue 3 UI at http://localhost:5173
- WebSocket endpoint at ws://localhost:8000/ws/status
- Full feature parity with Epic 5 stories 5.1-5.5
- Updated documentation and deployment guides

---

## Story 7.2: Application History and Search (Deferred from Epic 5)

**Status:** Planned (Pending Story 7.1 completion)

**As a** user
**I want to** search and view my application history in the new Vue 3 UI
**So that** I can track which jobs I've applied to and when

**Context:** Story 5.6 was deferred from Epic 5 to V2 development. Now that we're building a new frontend, we can implement this feature with better search, filtering, and export capabilities using Vue 3's component ecosystem.

**Acceptance Criteria:**
1. Application history table with all completed applications
2. Advanced search and filtering (title, company, platform, date range, match score)
3. Sortable columns with persistent sort preferences
4. Application detail modal with full information
5. Export to CSV functionality
6. Statistics and trend visualization
7. Pagination and infinite scroll support

**Dependencies:**
- Story 7.1 must be complete (Vue 3 infrastructure in place)
- Backend `/api/history` endpoint (may need creation)

**Technical Notes:**
- Use Vue 3 components for table and modals
- Implement client-side filtering for better performance
- Use Chart.js or similar for trend visualization
- Leverage Pinia store for state management

---

## Story 7.3: Enhanced UI/UX Improvements (Future)

**Status:** Planned (V2 Enhancement)

**As a** user
**I want** an enhanced user interface with advanced features
**So that** I have a better experience managing my job applications

**Potential Enhancements:**
- Dark mode support
- Customizable dashboard layouts
- Job detail modal with full information
- Edit CV/CL before approval workflow
- Advanced filtering and saved searches
- Keyboard shortcuts for power users
- Mobile-responsive improvements
- Toast notifications for real-time events
- User preferences persistence

**Dependencies:**
- Story 7.1 complete
- Story 7.2 complete (optional)

---

## Epic 7 Definition of Done

- [x] Story updated with Docker-first approach (2025-10-30) ✅
- [ ] Story 7.1: Vue 3 Frontend Migration complete with all AC met
- [ ] All Epic 5 functionality (5.1-5.5) working in Vue 3 UI
- [ ] WebSocket real-time updates functional
- [ ] Gradio completely removed from codebase
- [ ] Docker Compose starts frontend + backend successfully
- [ ] Frontend accessible at http://localhost:5173
- [ ] Backend API accessible at http://localhost:8000
- [ ] All tests passing (WebSocket, component, integration)
- [ ] Documentation updated (README, deployment guides)
- [ ] Story 7.2: Application History implemented (stretch goal)
- [ ] Zero regression from Epic 5 functionality
- [ ] Code review completed with Grade A or higher
- [ ] QA verification completed
- [ ] Production deployment successful

---

## Technical Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Browser Client                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │            Vue 3 Frontend (Port 5173)                │   │
│  │  ┌────────────┐  ┌──────────┐  ┌────────────────┐  │   │
│  │  │ Components │  │  Pinia   │  │  API Client    │  │   │
│  │  │  - Dashboard│ │  Store   │  │  - HTTP (Axios)│  │   │
│  │  │  - JobTable │ │          │  │  - WebSocket   │  │   │
│  │  │  - Pipeline │ │          │  │                │  │   │
│  │  │  - Pending  │ │          │  │                │  │   │
│  │  └────────────┘  └──────────┘  └────────────────┘  │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                        │              │
                        │ HTTP         │ WebSocket
                        │ /api/*       │ /ws/status
                        ▼              ▼
┌─────────────────────────────────────────────────────────────┐
│               FastAPI Backend (Port 8000)                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  REST API Endpoints          WebSocket Manager      │   │
│  │  - GET /api/jobs             - ConnectionManager    │   │
│  │  - GET /api/pipeline         - broadcast()          │   │
│  │  - GET /api/pending          - Real-time updates    │   │
│  │  - POST /api/jobs/:id/retry                         │   │
│  │  - POST /api/pending/:id/approve                    │   │
│  └──────────────────────────────────────────────────────┘   │
│                         │                                    │
│  ┌─────────────────────┴────────────────────────────────┐   │
│  │          Existing Backend Components                 │   │
│  │  - Agent Pipeline (RQ Workers)                       │   │
│  │  - DuckDB Database                                   │   │
│  │  - Redis Queue                                       │   │
│  │  - Job Discovery Services                            │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

**Frontend:**
- **Framework:** Vue 3 (Composition API)
- **Build Tool:** Vite (fast HMR, optimized builds)
- **State Management:** Pinia (Vue 3 official state library)
- **HTTP Client:** Axios
- **Styling:** Tailwind CSS (utility-first)
- **WebSocket:** Native WebSocket API

**Backend (Unchanged):**
- **Framework:** FastAPI 0.100+ (WebSocket support)
- **Task Queue:** Redis + RQ
- **Database:** DuckDB
- **LLM:** Claude (Anthropic)

**DevOps:**
- **Containerization:** Docker + Docker Compose
- **Frontend Container:** node:18-alpine
- **Backend Container:** python:3.11-slim

### Data Flow

1. **Initial Load:**
   - Vue app loads → establishes WebSocket connection
   - Pinia store fetches initial data via HTTP API
   - Components render with initial state

2. **Real-time Updates:**
   - Backend events trigger WebSocket broadcasts
   - Frontend WebSocket client receives messages
   - Pinia store updates reactive state
   - Components auto-update via Vue reactivity

3. **User Actions:**
   - User clicks button → component emits event
   - Pinia action called → HTTP API request
   - Backend processes → updates database
   - Backend broadcasts WebSocket update
   - All connected clients receive update

---

## Risk Assessment & Mitigation

### Risk 1: Feature Parity Gaps
**Impact:** High | **Probability:** Medium

**Description:** Missing functionality from Gradio UI in Vue 3 implementation

**Mitigation:**
- Comprehensive feature checklist from Epic 5 stories
- Side-by-side testing of Gradio vs Vue 3 UI
- Gradio UI remains available until Vue 3 complete
- Story 7.1 AC explicitly covers all Epic 5 features

### Risk 2: WebSocket Reliability
**Impact:** Medium | **Probability:** Low

**Description:** WebSocket connection drops or fails to reconnect

**Mitigation:**
- Implement auto-reconnect with exponential backoff
- Fallback to HTTP polling if WebSocket unavailable (future enhancement)
- Comprehensive WebSocket testing in Task 8
- Connection status indicator in UI

### Risk 3: Docker Complexity
**Impact:** Low | **Probability:** Medium

**Description:** Docker Compose setup becomes complex with frontend service

**Mitigation:**
- Clear documentation in Story 7.1 Task 6
- Docker-first approach documented in Dev Notes
- Volume mounting for hot reload during development
- Separate production Dockerfile with optimized builds

### Risk 4: Learning Curve
**Impact:** Low | **Probability:** Low

**Description:** Development velocity slows due to new tech stack

**Mitigation:**
- Comprehensive Dev Notes with examples
- Vue 3 is well-documented with large community
- Task breakdown provides step-by-step guidance
- Modern tooling (Vite, Pinia) reduces complexity

---

## Dependencies & Prerequisites

### Prerequisites
- Epic 5 complete (Gradio UI functional)
- Docker and Docker Compose installed
- Git repository with current codebase

### Internal Dependencies
- Existing FastAPI REST endpoints (from Epic 5)
- DuckDB schema and queries (unchanged)
- Redis + RQ worker infrastructure (unchanged)

### External Dependencies
- Node.js 18+ (via Docker container)
- npm packages: Vue 3, Vite, Pinia, Axios, Tailwind CSS
- Browser with WebSocket support (all modern browsers)

---

## Testing Strategy

### Unit Testing
- **Backend:** pytest for WebSocket ConnectionManager
- **Frontend:** Vitest for Pinia store and utility functions (optional for MVP)

### Integration Testing
- WebSocket connection and message handling
- API client integration with FastAPI endpoints
- State management flow (HTTP → Pinia → Components)

### Manual Testing
- Functional testing of all UI components
- WebSocket real-time update verification
- Cross-browser testing (Chrome, Firefox, Safari)
- Responsive design testing (desktop, tablet, mobile)

### Regression Testing
- Compare Vue 3 UI functionality against Epic 5 checklist
- Verify all Epic 5 stories (5.1-5.5) work identically
- No backend functionality regressions

---

## Rollout Strategy

### Phase 1: Development (Week 8, Days 1-3)
- Complete Story 7.1 Tasks 1-6 (Backend WebSocket + Vue 3 Frontend)
- Docker Compose running with both services
- Basic functional testing

### Phase 2: Gradio Removal (Week 8, Day 4)
- Complete Story 7.1 Task 7 (Remove Gradio)
- Comprehensive testing in Task 8
- QA verification

### Phase 3: Documentation & Deployment (Week 8, Day 5)
- Complete Story 7.1 Task 9 (Documentation)
- Production deployment preparation
- User acceptance testing

### Phase 4: Production (Week 8, End)
- Deploy Vue 3 UI to production
- Monitor WebSocket connections and performance
- Gradio UI removed from codebase

---

## Success Metrics

### Technical Metrics
- **Feature Parity:** 100% (all Epic 5 functionality present)
- **WebSocket Uptime:** >99% (reliable real-time updates)
- **Page Load Time:** <2 seconds (initial load)
- **Hot Reload:** <200ms (component updates during development)
- **Test Coverage:** >85% (WebSocket code)
- **Build Time:** <30 seconds (production build)

### User Experience Metrics
- **Real-time Latency:** <500ms (event to UI update)
- **Responsive Design:** Works on mobile, tablet, desktop
- **Zero Regression:** No lost functionality from Epic 5

### Development Metrics
- **Code Quality:** Grade A or higher on code review
- **Documentation:** Comprehensive README and deployment guides
- **Zero Technical Debt:** No deferred refactoring

---

## Future Enhancements (Post-Epic 7)

### Phase 2 Features (V2)
- Story 7.2: Application History and Search
- Story 7.3: Enhanced UI/UX (dark mode, advanced filtering)
- User authentication and multi-user support
- Job detail modal with full information editing
- Advanced analytics and reporting dashboard
- Mobile native app (React Native or similar)

### Technical Improvements
- Frontend unit testing with Vitest
- E2E testing with Playwright
- CI/CD pipeline for frontend builds
- CDN deployment for static assets
- Server-Side Rendering (SSR) with Nuxt.js (if needed)

---

## Epic 7 Retrospective (Post-Completion)

_To be filled after Epic 7 completion_

### What Went Well
- TBD

### What Could Be Improved
- TBD

### Key Learnings
- TBD

### Action Items for Next Epic
- TBD

---

## References

- **Epic 5:** Gradio UI (docs/prd/epic-5-gradio-ui.md)
- **Story 7.1:** Vue 3 Frontend Migration (docs/stories/7.1.vue3-frontend-migration.md)
- **Migration Guide:** GRADIO_TO_VUE3_MIGRATION.md
- **Architecture:** docs/architecture/12-technology-stack.md
- **Tech Stack:** docs/architecture/13-implementation-patterns.md

---

**Epic Status:** In Progress ⏳
**Created:** 2025-10-30
**Updated:** 2025-10-30
**Owner:** Product Team
