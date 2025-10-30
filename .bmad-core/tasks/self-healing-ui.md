# Self-Healing Dashboard UI System
## Iterative Dark Theme Development with Modern Tools

## Overview
Automated UI development and validation system using Playwright MCP, TailwindCSS Server MCP, and shadcn-vue MCP to iteratively build, validate, and improve a modern dark theme dashboard UI.

## System Architecture

### Core Components
- **Playwright MCP**: Browser automation for live UI testing, screenshot capture, and interaction validation
- **TailwindCSS Server MCP**: Real-time access to TailwindCSS utilities, color palettes, and configurations
- **shadcn-vue MCP**: Component library access for Vue 3 dashboard components with dark theme support
- **Visual Validator**: AI-powered screenshot analysis to validate UI against design requirements
- **Code Generator**: Automatically generates and updates Vue 3 components with TailwindCSS
- **Feedback Loop**: Iterative improvement cycle with validation and auto-fixes

## Iterative Development Process

### Step 1: Initialize Dashboard UI Foundation

Set up the Vue 3 dashboard structure with shadcn-vue components and TailwindCSS dark theme.

**1.1: Query shadcn-vue for Dashboard Components**
```javascript
// Get available dashboard components
const components = await mcp__shadcn__search_items_in_registries({
  registries: ["@shadcn"],
  query: "dashboard card sidebar"
});

// Get specific component details
const cardComponent = await mcp__shadcn__view_items_in_registries({
  items: ["@shadcn/card", "@shadcn/sidebar", "@shadcn/chart"]
});

// Get example implementations
const examples = await mcp__shadcn__get_item_examples_from_registries({
  registries: ["@shadcn"],
  query: "dashboard-demo example"
});
```

**1.2: Get TailwindCSS Dark Theme Configuration**
```javascript
// Get dark theme color palette
const darkColors = await mcp__tailwindcss-server__get_tailwind_colors({
  colorName: "slate",
  includeShades: true
});

// Get layout utilities
const layoutUtils = await mcp__tailwindcss-server__get_tailwind_utilities({
  category: "layout"
});

// Get custom color palette for dashboard
const palette = await mcp__tailwindcss-server__generate_color_palette({
  baseColor: "#1e293b", // slate-800 as base
  name: "dashboard",
  shades: [50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950]
});
```

**1.3: Generate Initial Dashboard Structure**
```vue
<!-- Generated frontend/src/views/Dashboard.vue -->
<template>
  <div class="min-h-screen bg-slate-950">
    <Sidebar class="fixed left-0 top-0 h-full" />
    <main class="ml-64 p-6">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <StatsCard v-for="stat in stats" :key="stat.id" :data="stat" />
      </div>
      <div class="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartCard type="line" :data="chartData" />
        <ChartCard type="bar" :data="chartData" />
      </div>
    </main>
  </div>
</template>
```

**Output:**
```json
{
  "iteration": 0,
  "files_created": [
    "frontend/src/views/Dashboard.vue",
    "frontend/src/components/Sidebar.vue",
    "frontend/src/components/StatsCard.vue",
    "frontend/src/components/ChartCard.vue"
  ],
  "components_installed": ["card", "sidebar", "chart"],
  "timestamp": "2025-10-30T14:30:22Z",
  "status": "initialized"
}
```

### Step 2: Visual Validation with Playwright

Launch the development server and validate the live UI using Playwright browser automation.

**2.1: Start Development Server & Navigate**
```javascript
// Launch dev server in background
await bash_run_in_background("npm run dev", { cwd: "./frontend" });

// Wait for server to be ready
await wait(3000);

// Navigate to dashboard
await mcp__playwright__browser_navigate({
  url: "http://localhost:5173/dashboard"
});

// Wait for page to load
await mcp__playwright__browser_wait_for({
  text: "Dashboard",
  time: 5
});
```

**2.2: Capture UI State**
```javascript
// Take accessibility snapshot (better than screenshot for analysis)
const snapshot = await mcp__playwright__browser_snapshot();

// Take visual screenshot for reference
const screenshot = await mcp__playwright__browser_take_screenshot({
  fullPage: true,
  filename: "dashboard-iteration-1.png"
});

// Get console errors
const consoleErrors = await mcp__playwright__browser_console_messages({
  onlyErrors: true
});

// Check network requests
const networkRequests = await mcp__playwright__browser_network_requests();
```

**2.3: Dark Theme Validation Criteria (Score 1-10)**

| Criterion | Weight | Description | Validation Method |
|-----------|--------|-------------|-------------------|
| Dark Background | 20% | Proper dark slate/gray tones (bg-slate-900/950) | Analyze snapshot for background colors |
| Color Contrast | 20% | WCAG AA compliance for text on dark backgrounds | Check text contrast ratios |
| Component Styling | 15% | shadcn-vue components properly themed | Verify dark mode classes applied |
| Interactive States | 15% | Hover, focus, active states visible on dark | Test interactions with Playwright |
| Typography | 10% | Readable text with proper text colors | Check text-slate-50/100 usage |
| Spacing & Layout | 10% | Consistent padding, margins, grid structure | Measure element spacing |
| Responsiveness | 5% | Mobile, tablet, desktop breakpoints | Test different viewport sizes |
| Accessibility | 5% | Keyboard navigation, ARIA labels | Check accessibility tree |

**Pass Threshold:** `8.0/10` (Modern dashboard standard)

### Step 3: Automated Code Remediation

Analyze validation results and automatically fix issues in Vue components.

```javascript
async function ui_remediation(validationResults, iteration) {
    const score = validationResults.score;

    if (score < 8.0) {
        console.log(`Iteration ${iteration}: Score ${score}/10 - Applying fixes...`);

        // Auto-fix what we can
        for (const violation of validationResults.violations) {
            if (violation.autoFixable) {
                await applyCodeFix(violation);
            } else {
                console.log(`Manual review needed: ${violation.description}`);
            }
        }

        // Hot-reload should trigger automatically
        await wait(2000);

        // Re-validate
        return "requires_revalidation";
    }

    console.log(`Iteration ${iteration}: Score ${score}/10 - PASSED ✓`);
    return "approved";
}
```

**3.1: Auto-Fixable Violations**

**Dark Background Issues**
```javascript
// Issue: Light background detected
// Fix: Update to dark slate
await editVueFile("Dashboard.vue", {
  oldClass: "bg-white",
  newClass: "bg-slate-950"
});

// Get proper dark colors from TailwindCSS
const darkBg = await mcp__tailwindcss-server__get_tailwind_utilities({
  category: "colors",
  property: "background-color"
});
```

**Low Color Contrast**
```javascript
// Issue: Text not readable on dark background
// Fix: Update text color
await editVueFile("StatsCard.vue", {
  oldClass: "text-gray-600",
  newClass: "text-slate-100"
});

// Verify contrast ratio
const contrastCheck = await analyzeContrast({
  background: "#020617", // slate-950
  foreground: "#f1f5f9"  // slate-100
});
// Should be >= 4.5 for WCAG AA
```

**Missing shadcn-vue Component Styling**
```javascript
// Issue: Custom card styling instead of shadcn
// Fix: Replace with shadcn Card component
const cardComponent = await mcp__shadcn__view_items_in_registries({
  items: ["@shadcn/card"]
});

// Apply shadcn Card structure
await replaceComponent({
  file: "StatsCard.vue",
  oldComponent: "CustomCard",
  newComponent: "Card",
  withClasses: "bg-slate-900 border-slate-800 text-slate-100"
});
```

**Interactive State Issues**
```javascript
// Issue: Hover states not visible on dark theme
// Fix: Add proper hover classes
await addTailwindClasses("Button.vue", {
  element: "button",
  classes: [
    "hover:bg-slate-800",
    "focus:ring-2",
    "focus:ring-slate-600",
    "active:bg-slate-700",
    "transition-colors"
  ]
});
```

**3.2: Manual Review Categories**
- Complex layout restructuring
- Custom animation implementations
- Performance optimizations
- Advanced accessibility features

## Robustness Enhancements

### Error Handling & Recovery

```javascript
class UIValidator {
  async validateWithRetry(url, maxRetries = 3) {
    let retries = 0;
    let lastError = null;

    while (retries < maxRetries) {
      try {
        // Check if browser is open
        const browserReady = await this.checkBrowser();
        if (!browserReady) {
          await mcp__playwright__browser_navigate({ url });
        }

        // Validate UI
        const result = await this.validateUI();
        return result;

      } catch (error) {
        lastError = error;
        retries++;

        console.log(`Validation attempt ${retries} failed: ${error.message}`);

        // Exponential backoff
        await this.wait(Math.pow(2, retries) * 1000);

        // Try browser restart on final retry
        if (retries === maxRetries - 1) {
          await this.restartBrowser();
          return await this.validateUI();
        }
      }
    }

    throw new Error(`Validation failed after ${maxRetries} attempts: ${lastError}`);
  }

  async restartBrowser() {
    console.log("Restarting browser...");
    await mcp__playwright__browser_close();
    await wait(1000);
    await mcp__playwright__browser_navigate({ url: this.dashboardUrl });
  }
}
```

### Incremental Validation

```javascript
// Validate only changed components since last iteration
async function incrementalValidation(iteration) {
  const lastCheckpoint = await loadCheckpoint(`iteration-${iteration - 1}`);

  // Get current file timestamps
  const currentFiles = await getFileTimestamps("frontend/src/**/*.vue");

  const changedFiles = detectChanges(lastCheckpoint.files, currentFiles);

  if (changedFiles.length === 0) {
    console.log("No changes detected, skipping validation");
    return { status: "no_changes", score: lastCheckpoint.score };
  }

  console.log(`Changed files: ${changedFiles.join(", ")}`);

  // Hot-reload will handle updates, wait for it
  await wait(2000);

  // Validate UI
  const result = await validateUI();

  await saveCheckpoint(`iteration-${iteration}`, currentFiles, result);
  return result;
}
```

### Component-Level Testing

```javascript
// Test individual components in isolation
async function testComponents(components) {
  const results = [];

  for (const component of components) {
    console.log(`Testing ${component.name}...`);

    // Navigate to component story/demo
    await mcp__playwright__browser_navigate({
      url: `http://localhost:5173/test/${component.name}`
    });

    // Test interactions
    if (component.interactive) {
      await testInteractions(component);
    }

    // Take screenshot
    await mcp__playwright__browser_take_screenshot({
      filename: `${component.name}-test.png`
    });

    // Validate styling
    const validation = await validateComponentStyling(component);
    results.push(validation);
  }

  return results;
}

async function testInteractions(component) {
  const snapshot = await mcp__playwright__browser_snapshot();

  // Find interactive elements
  const buttons = findElements(snapshot, "button");

  for (const button of buttons) {
    // Test hover state
    await mcp__playwright__browser_hover({
      element: button.name,
      ref: button.ref
    });
    await wait(200);

    // Test click
    await mcp__playwright__browser_click({
      element: button.name,
      ref: button.ref
    });
    await wait(500);
  }
}
```

## MCP Tools Configuration

```yaml
ui_development_config:
  # Playwright settings
  playwright:
    browser: "chromium"
    headless: false  # Set to false to watch iterations
    viewport:
      width: 1920
      height: 1080
    dev_server:
      url: "http://localhost:5173"
      startup_delay: 3000  # ms
    screenshot_dir: "./screenshots"

  # TailwindCSS Server settings
  tailwindcss:
    framework: "vue"
    dark_mode: "class"  # or "media"
    primary_colors:
      - "slate"
      - "zinc"
      - "gray"
    custom_palette:
      base_color: "#1e293b"
      name: "dashboard"
    utilities_to_query:
      - "layout"
      - "colors"
      - "typography"
      - "spacing"

  # shadcn-vue settings
  shadcn:
    registries: ["@shadcn"]
    components_to_use:
      - "card"
      - "button"
      - "sidebar"
      - "chart"
      - "table"
      - "dialog"
      - "dropdown-menu"
    style: "modern"  # minimal, modern, playful
    dark_mode: true
    responsive: true

  # Validation settings
  validation:
    score_threshold: 8.0
    max_iterations: 5
    iteration_delay: 2000  # ms
    auto_fix: true
    screenshot_on_pass: true
    screenshot_on_fail: true
```

## Iterative Development Loop

```javascript
async function iterativeDevelopment() {
  let iteration = 0;
  let lastScore = 0;
  const maxIterations = 5;
  const scoreThreshold = 8.0;

  console.log("🚀 Starting iterative UI development...");

  // Step 1: Initialize
  await initializeDashboard();

  while (iteration < maxIterations) {
    iteration++;
    console.log(`\n=== Iteration ${iteration} ===`);

    // Step 2: Validate
    const validation = await validateUI();
    console.log(`Score: ${validation.score}/10`);

    // Check exit conditions
    if (validation.score >= scoreThreshold) {
      console.log(`✓ PASSED! Score ${validation.score} meets threshold ${scoreThreshold}`);
      await captureSuccessScreenshot(iteration);
      break;
    }

    if (iteration === maxIterations) {
      console.log(`⚠ Max iterations reached. Final score: ${validation.score}/10`);
      break;
    }

    if (validation.score <= lastScore && iteration > 1) {
      console.log(`⚠ No improvement detected. Score unchanged at ${validation.score}`);
      console.log("Manual review recommended.");
      break;
    }

    // Step 3: Apply fixes
    console.log(`Applying ${validation.violations.length} fixes...`);
    await applyFixes(validation.violations);

    lastScore = validation.score;

    // Wait for hot-reload
    await wait(2000);
  }

  // Generate final report
  await generateReport(iteration, lastScore);
}
```

## Exit Conditions

The development loop terminates when:
- **SUCCESS**: UI achieves score ≥ 8.0/10
- **MAX ITERATIONS**: Reached 5 iterations without passing
- **NO IMPROVEMENT**: Score hasn't improved for 2 consecutive iterations
- **MANUAL OVERRIDE**: Developer intervention requested
- **CRITICAL ERROR**: Build fails or server crashes

## Validation Report

Generated at: `reports/dashboard-ui-validation-{date}.json`

```json
{
  "project": {
    "name": "Job Matcher Dashboard",
    "frontend_path": "./frontend",
    "framework": "Vue 3",
    "styling": "TailwindCSS + shadcn-vue"
  },
  "validation_summary": {
    "validation_id": "uuid-v4",
    "timestamp": "2025-10-30T16:00:00Z",
    "total_iterations": 3,
    "final_score": 8.4,
    "status": "PASSED",
    "duration_seconds": 47
  },
  "iteration_history": [
    {
      "iteration": 1,
      "score": 5.2,
      "violations": 12,
      "fixes_applied": 8,
      "screenshot": "dashboard-iteration-1.png"
    },
    {
      "iteration": 2,
      "score": 7.1,
      "violations": 5,
      "fixes_applied": 4,
      "screenshot": "dashboard-iteration-2.png"
    },
    {
      "iteration": 3,
      "score": 8.4,
      "violations": 0,
      "fixes_applied": 1,
      "screenshot": "dashboard-iteration-3.png"
    }
  ],
  "violations_found": [
    {
      "iteration": 1,
      "component": "Dashboard.vue",
      "violation_type": "dark_background",
      "description": "Light background detected, should use bg-slate-950",
      "current": "bg-white",
      "expected": "bg-slate-950",
      "severity": "high",
      "auto_fixed": true,
      "fix_applied": "Updated class from bg-white to bg-slate-950"
    },
    {
      "iteration": 1,
      "component": "StatsCard.vue",
      "violation_type": "color_contrast",
      "description": "Text not readable on dark background",
      "current": "text-gray-600",
      "expected": "text-slate-100",
      "severity": "high",
      "auto_fixed": true,
      "fix_applied": "Updated text color for WCAG AA compliance"
    },
    {
      "iteration": 2,
      "component": "Button.vue",
      "violation_type": "interactive_states",
      "description": "Hover state not visible on dark theme",
      "current": "hover:bg-gray-100",
      "expected": "hover:bg-slate-800 focus:ring-2 focus:ring-slate-600",
      "severity": "medium",
      "auto_fixed": true,
      "fix_applied": "Added dark-theme hover and focus states"
    }
  ],
  "auto_fixes_applied": [
    {
      "iteration": 1,
      "file": "Dashboard.vue",
      "fix_type": "background_color",
      "old_class": "bg-white",
      "new_class": "bg-slate-950",
      "status": "success"
    },
    {
      "iteration": 2,
      "file": "Sidebar.vue",
      "fix_type": "component_replacement",
      "description": "Replaced custom sidebar with shadcn Sidebar component",
      "status": "success"
    }
  ],
  "performance_metrics": {
    "total_duration_ms": 47230,
    "avg_iteration_time_ms": 15743,
    "playwright_operations": 18,
    "tailwindcss_queries": 12,
    "shadcn_queries": 6,
    "files_modified": 5
  },
  "final_state": {
    "dark_theme_compliance": 95,
    "contrast_ratio_min": 4.8,
    "shadcn_components_used": ["Card", "Button", "Sidebar", "Chart"],
    "tailwind_utilities_used": 127,
    "accessibility_score": 92,
    "responsive_breakpoints_tested": ["mobile", "tablet", "desktop"]
  },
  "recommendations": [
    "Consider adding loading skeletons for better UX",
    "Implement error boundary components",
    "Add unit tests for interactive components",
    "Document dark theme color tokens"
  ],
  "screenshots": {
    "initial": "dashboard-iteration-1.png",
    "final": "dashboard-iteration-3-success.png",
    "mobile": "dashboard-mobile.png",
    "tablet": "dashboard-tablet.png"
  }
}
```

## Complete Workflow Example

```javascript
// Full iterative UI development workflow
async function developDashboardUI() {
  console.log("=== Dashboard UI Development Workflow ===\n");

  // Phase 1: Discover shadcn components
  console.log("Phase 1: Discovering components...");
  const components = await mcp__shadcn__search_items_in_registries({
    registries: ["@shadcn"],
    query: "dashboard card sidebar chart"
  });
  console.log(`Found ${components.length} components`);

  // Get component examples
  const examples = await mcp__shadcn__get_item_examples_from_registries({
    registries: ["@shadcn"],
    query: "dashboard-demo"
  });

  // Phase 2: Query TailwindCSS utilities
  console.log("\nPhase 2: Getting TailwindCSS dark theme utilities...");
  const darkColors = await mcp__tailwindcss-server__get_tailwind_colors({
    colorName: "slate",
    includeShades: true
  });

  const layoutUtils = await mcp__tailwindcss-server__get_tailwind_utilities({
    category: "layout"
  });

  // Phase 3: Generate initial components
  console.log("\nPhase 3: Generating components...");
  await generateDashboardComponents(components, darkColors);

  // Phase 4: Start dev server
  console.log("\nPhase 4: Starting development server...");
  await startDevServer();

  // Phase 5: Iterative validation & improvement
  console.log("\nPhase 5: Starting iterative improvements...");
  let iteration = 0;
  let lastScore = 0;
  const maxIterations = 5;
  const scoreThreshold = 8.0;

  while (iteration < maxIterations) {
    iteration++;
    console.log(`\n--- Iteration ${iteration} ---`);

    // Navigate to dashboard
    await mcp__playwright__browser_navigate({
      url: "http://localhost:5173/dashboard"
    });

    // Capture state
    const snapshot = await mcp__playwright__browser_snapshot();
    const screenshot = await mcp__playwright__browser_take_screenshot({
      fullPage: true,
      filename: `dashboard-iteration-${iteration}.png`
    });

    // Validate
    const validation = await validateDarkTheme(snapshot);
    console.log(`Score: ${validation.score}/10`);

    // Check exit conditions
    if (validation.score >= scoreThreshold) {
      console.log(`✓ SUCCESS! Dashboard passed validation.`);
      await captureSuccessScreenshots();
      break;
    }

    if (iteration === maxIterations) {
      console.log(`⚠ Max iterations reached.`);
      break;
    }

    // Apply fixes
    console.log(`Applying ${validation.violations.length} fixes...`);
    for (const violation of validation.violations) {
      await applyFix(violation);
    }

    lastScore = validation.score;
    await wait(2000); // Wait for hot-reload
  }

  // Phase 6: Generate report
  console.log("\n\nPhase 6: Generating report...");
  await generateFinalReport(iteration, lastScore);

  console.log("\n=== Workflow Complete ===");
}

// Helper function to validate dark theme
async function validateDarkTheme(snapshot) {
  const violations = [];
  let score = 10;

  // Check background colors
  const backgrounds = extractBackgrounds(snapshot);
  for (const bg of backgrounds) {
    if (!isDarkColor(bg.color)) {
      violations.push({
        type: "dark_background",
        component: bg.component,
        current: bg.color,
        expected: "bg-slate-950",
        severity: "high",
        autoFixable: true
      });
      score -= 2;
    }
  }

  // Check text contrast
  const textElements = extractTextElements(snapshot);
  for (const text of textElements) {
    const contrast = calculateContrast(text.color, text.background);
    if (contrast < 4.5) {
      violations.push({
        type: "color_contrast",
        component: text.component,
        current: `Contrast ratio: ${contrast}`,
        expected: "≥ 4.5 (WCAG AA)",
        severity: "high",
        autoFixable: true
      });
      score -= 1.5;
    }
  }

  // Check interactive states
  const interactiveElements = extractInteractiveElements(snapshot);
  for (const elem of interactiveElements) {
    if (!hasHoverState(elem)) {
      violations.push({
        type: "interactive_states",
        component: elem.component,
        description: "Missing hover/focus states",
        severity: "medium",
        autoFixable: true
      });
      score -= 0.5;
    }
  }

  return {
    score: Math.max(0, score),
    violations,
    passed: score >= 8.0
  };
}
```

## Project Configuration

`dashboard-ui-config.json`:
```json
{
  "project": {
    "name": "Job Matcher Dashboard",
    "frontend_dir": "./frontend",
    "framework": "Vue 3",
    "package_manager": "npm"
  },
  "dev_server": {
    "url": "http://localhost:5173",
    "startup_command": "npm run dev",
    "startup_delay_ms": 3000,
    "hot_reload": true
  },
  "playwright": {
    "browser": "chromium",
    "headless": false,
    "viewport": {
      "width": 1920,
      "height": 1080
    },
    "screenshot_dir": "./screenshots",
    "video_dir": "./videos"
  },
  "tailwindcss": {
    "config_file": "./frontend/tailwind.config.js",
    "dark_mode": "class",
    "theme": {
      "colors": {
        "primary": "slate",
        "background": "slate-950",
        "foreground": "slate-50",
        "card": "slate-900",
        "card-foreground": "slate-100"
      },
      "spacing": "default",
      "typography": "default"
    }
  },
  "shadcn": {
    "registries": ["@shadcn"],
    "components_dir": "./frontend/src/components/ui",
    "style": "modern",
    "dark_mode": true,
    "responsive": true,
    "preferred_components": [
      "card",
      "button",
      "sidebar",
      "chart",
      "table",
      "dialog",
      "dropdown-menu",
      "tabs",
      "toast"
    ]
  },
  "validation": {
    "score_threshold": 8.0,
    "max_iterations": 5,
    "iteration_delay_ms": 2000,
    "auto_fix": true,
    "criteria": {
      "dark_background": 2.0,
      "color_contrast": 2.0,
      "component_styling": 1.5,
      "interactive_states": 1.5,
      "typography": 1.0,
      "spacing_layout": 1.0,
      "responsiveness": 0.5,
      "accessibility": 0.5
    }
  },
  "reporting": {
    "output_dir": "./reports",
    "format": ["json", "markdown"],
    "include_screenshots": true,
    "track_history": true,
    "generate_comparison": true
  }
}
```

## Implementation Checklist

### Initial Setup
- [ ] Configure Playwright MCP for browser automation
- [ ] Set up TailwindCSS Server MCP connection
- [ ] Configure shadcn-vue MCP for component access
- [ ] Create `dashboard-ui-config.json`
- [ ] Set up screenshot and report directories
- [ ] Ensure Vue 3 frontend is properly configured

### Component Discovery
- [ ] Query shadcn-vue for dashboard components
- [ ] Get component examples and demos
- [ ] Review shadcn Card, Button, Sidebar, Chart components
- [ ] Get add commands for required components
- [ ] Install components using CLI

### Dark Theme Setup
- [ ] Query TailwindCSS for slate color palette
- [ ] Generate custom color palette if needed
- [ ] Get dark theme utilities (backgrounds, text, borders)
- [ ] Configure dark mode in tailwind.config.js
- [ ] Set up color scheme variables

### Initial UI Generation
- [ ] Create Dashboard.vue with dark background
- [ ] Generate StatsCard component with shadcn Card
- [ ] Create Sidebar component with shadcn Sidebar
- [ ] Add ChartCard components with shadcn Chart
- [ ] Set up routing to dashboard view

### Playwright Automation
- [ ] Start development server
- [ ] Configure browser viewport (1920x1080)
- [ ] Set up navigation to dashboard URL
- [ ] Configure screenshot capture settings
- [ ] Test browser snapshot functionality

### Iterative Validation
- [ ] Implement dark theme validation logic
- [ ] Set up color contrast checking (WCAG AA)
- [ ] Configure interactive state testing
- [ ] Implement responsive breakpoint testing
- [ ] Set up scoring system (0-10)

### Auto-Fix System
- [ ] Implement background color fixes
- [ ] Configure text color contrast fixes
- [ ] Set up interactive state class additions
- [ ] Implement shadcn component replacements
- [ ] Configure spacing and layout fixes

### Testing & Quality
- [ ] Test component-level interactions
- [ ] Verify hover and focus states
- [ ] Check keyboard navigation
- [ ] Test mobile responsiveness
- [ ] Validate accessibility tree

### Reporting & Documentation
- [ ] Configure JSON report generation
- [ ] Set up iteration history tracking
- [ ] Generate before/after screenshots
- [ ] Create markdown summary reports
- [ ] Document auto-fixes applied

## Best Practices & Tips

### Playwright Best Practices
- **Headless Mode**: Set to `false` during development to watch iterations
- **Wait Strategies**: Always wait for elements before interactions
- **Screenshots**: Capture both snapshot and screenshot for analysis
- **Error Handling**: Implement retry logic for flaky tests
- **Browser Cleanup**: Close browser sessions properly

### TailwindCSS Dark Theme
- **Color Consistency**: Use slate palette consistently (950, 900, 800, etc.)
- **Contrast Ratios**: Aim for ≥ 4.5 for WCAG AA compliance
- **Interactive States**: Always define hover, focus, and active states
- **Dark Mode Class**: Use `dark:` prefix or `class` strategy
- **Custom Colors**: Generate palettes for brand colors

### shadcn-vue Components
- **Component Style**: Choose modern style for dashboard aesthetics
- **Dark Mode Support**: Ensure all components have dark variants
- **Customization**: Use TailwindCSS classes to customize
- **Examples First**: Always review examples before implementation
- **Composition**: Build complex UIs from simpler components

### Iterative Development
- **Start Simple**: Begin with basic layout, improve iteratively
- **Small Fixes**: Apply one fix at a time for clarity
- **Hot Reload**: Leverage Vite's hot-reload for fast iterations
- **Score Tracking**: Monitor score improvement between iterations
- **Exit Early**: Stop if score plateaus to avoid wasted effort

### Performance Optimization
- **Iteration Delay**: 2-3 seconds between iterations for hot-reload
- **Screenshot Size**: Use viewport screenshots instead of full page when possible
- **Snapshot First**: Prefer browser snapshots over screenshots for validation
- **Incremental Validation**: Only re-check changed components
- **Cache Results**: Store successful validations to skip re-checks

### Common Pitfalls
- **Light Backgrounds**: Always check for accidental light backgrounds
- **Poor Contrast**: Text on dark backgrounds needs proper contrast
- **Missing States**: Don't forget hover/focus/active states
- **Hard-coded Colors**: Use TailwindCSS classes, not inline styles
- **Component Inconsistency**: Use shadcn components uniformly