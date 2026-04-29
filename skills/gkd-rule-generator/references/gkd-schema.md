# GKD Subscription Schema Reference

## Subscription Root

```json5
{
  id: -2,          // Unique subscription ID (negative for local)
  name: '本地订阅',  // Subscription name
  version: 7,       // Increment on each update
  author: 'Author', // Optional
  updateUrl: '',    // Optional: remote update URL
  checkUpdateUrl: '', // Optional: version check URL
  supportUri: '',   // Optional: support link
  categories: [],   // Rule categories
  globalGroups: [], // Global rules applying to all apps
  apps: []          // App-specific rules
}
```

## App Structure

```json5
{
  id: 'com.example.app',  // Android package name
  name: '应用名称',        // Display name
  groups: []              // Rule groups for this app
}
```

## Group Structure

```json5
{
  key: 1,                    // Unique within app (auto-increment)
  name: '开屏广告',          // Group name
  desc: '跳过开屏广告',      // Optional description
  enable: true,              // Default enabled
  order: 0,                  // Display order
  actionCd: 3000,           // Optional: cooldown ms
  actionMaximum: 1,          // Optional: max actions per trigger
  matchTime: 10000,         // Optional: match timeout ms
  resetMatch: 'app',         // Optional: reset strategy
  rules: []                  // Rule variants
}
```

## Rule Structure

```json5
{
  key: 0,                    // Unique within group
  name: '跳过按钮',          // Rule name
  action: 'click',           // Action type
  matches: ['[vid="skip"]'], // Selector array
  excludeMatches: [],        // Optional: exclusion selectors
  activityIds: [],         // Optional: limit to activities
  excludeActivityIds: [],    // Optional: exclude activities
  snapshotUrls: [],        // Reference snapshots
  fastQuery: true,          // Enable query optimization
  matchDelay: 500,          // Optional: delay before match
  position: {              // Optional: click position
    left: '100',
    top: '200',
    right: '300',
    bottom: '400'
  }
}
```

## Action Types

| Action | Description |
|--------|-------------|
| `click` | Click element center |
| `clickCenter` | Explicit center click |
| `clickCenterX` | Click horizontal center |
| `clickCenterY` | Click vertical center |
| `back` | Press back button |
| `swipe` | Swipe gesture (requires position) |

## Selector Syntax

### Basic Selectors

```
[id="com.app:id/view"]     // Resource ID
[vid="view_id"]            // View ID (simplified)
[text="精确匹配"]           // Exact text match
[text^="前缀匹配"]          // Text starts with
[text$="后缀匹配"]          // Text ends with
[text*="包含匹配"]          // Text contains
[desc="描述内容"]           // Content description
[name="ClassName"]         // Class name
[clickable=true]           // Property match
[visibleToUser=true]       // Visibility
```

### Position Selectors

```
[left=100]                 // Exact left position
[left>100]                 // Greater than
[left<100]                 // Less than
[top>100][top<200]         // Range
```

### Combinators

```
A > B                      // Direct child
A < B                      // Direct parent
A + B                      // Adjacent sibling
A ~ B                      // General sibling
A B                        // Descendant
```

### Complex Examples

```
[vid="parent"] > [vid="child"]           // Direct child
[desc="弹窗"] < [clickable=true]          // Parent of dialog
[text="广告"] + [vid="close"]             // Sibling close button
[vid="container"] [text="跳过"]            // Descendant text
```

## Key Management

### Subscription ID
- Use negative numbers for local subscriptions
- Positive numbers reserved for remote subscriptions
- Must be unique globally

### App Key
- Unique within subscription
- Auto-increment starting from 1
- Never reuse deleted keys

### Group Key
- Unique within app
- Auto-increment starting from 1
- Stable across updates

### Rule Key
- Unique within group
- Starts from 0
- Multiple rules for fallback

## Validation Rules

1. All keys must be integers
2. No duplicate keys at same level
3. Selectors must be valid syntax
4. snapshotUrls should be valid URLs
5. activityIds should be full class names
