# Chapter 5: UI Components (Lipgloss)

Welcome back! In [Chapter 4: Tmux Session](04_tmux_session_.md), we saw how Claude Squad uses `tmux` to run AI agents in their own special terminal windows in the background. But how does Claude Squad take all that information – like lists of AI instances, their output, or code changes – and make it look nice and organized right in *your* main terminal?

This is where **UI Components** come in, and Claude Squad uses a special tool called **Lipgloss** to create them!

## What Problem Do UI Components Solve?

Imagine you're trying to build a LEGO castle. You have lots of bricks (each representing a bit of information or a piece of text) and you need to arrange them into a beautiful, functional structure. You can't just throw all the bricks into a pile and call it a castle! You need different types of bricks (like flat plates for floors, sloping bricks for roofs, or decorated bricks for windows) and rules for how they connect.

This is exactly what **UI Components** solve for your terminal application!

In a terminal user interface (TUI), everything is made of text and colors. UI Components are like the "building blocks" or "drawing tools" that let you arrange this text and color to create a clear and interactive display. Without them, Claude Squad would just be a jumbled mess of words.

A central use case for UI Components in Claude Squad is to **present complex information in an easy-to-understand, visual layout** within your terminal. Each part of the Claude Squad screen you see – the list of AI instances, the preview/diff area, the menu at the bottom, and even error messages – is a separate UI Component working together.

## How UI Components Work (The Basics)

Let's look at the main Claude Squad screen. It's not one giant piece; it's many smaller, specialized pieces, each handled by its own UI Component.

```
+------------------------------------+------------------------------------+
|  Instances (List Component)        |                                    |
|                                    |       Preview/Diff Pane            |
|  1. My First AI Instance (Running) |       (TabbedWindow Component)     |
|  2. Fix Bug Instance (Paused)      |                                    |
|                                    |                                    |
|  ... (more instances)              |                                    |
|                                    |                                    |
+------------------------------------+------------------------------------+
|          Menu (Menu Component)                                          |
+------------------------------------+------------------------------------+
|      Error Box (ErrBox Component)  (sometimes appears at the very bottom)
+-------------------------------------------------------------------------+
```

Each of these sections (the "List", the "Preview Pane", the "Menu", the "Error Box") is managed by a specific UI component. These components know how to:

1.  **Take data:** Like the name of an AI instance or the output from a [Tmux Session](04_tmux_session_.md).
2.  **Add style:** Use colors, borders, and spacing to make the text look good using Lipgloss.
3.  **Arrange themselves:** Work with the main application to fit into the overall screen layout.

### A Simple Example: The `List` Component

Let's take the `List` component (`ui/list.go`) as an example. Its job is to show you all your AI instances.

Here's how `List` uses Lipgloss to make things look good:

```go
// --- File: ui/list.go (Simplified) ---
package ui

import "github.com/charmbracelet/lipgloss" // Import Lipgloss!

// Define a style for the title of a selected item in the list
var selectedTitleStyle = lipgloss.NewStyle().
	Padding(1, 1, 0, 1).                 // Add space around the text
	Background(lipgloss.Color("#dde4f0")). // Set a light blue background
	Foreground(lipgloss.AdaptiveColor{Light: "#1a1a1a", Dark: "#1a1a1a"}) // Set dark text color

// Render method within the List component (simplified)
func (r *InstanceRenderer) Render(i *session.Instance, idx int, selected bool) string {
    // Determine which style to use based on whether the item is selected
    titleStyleToUse := titleStyle // Default style
    if selected {
        titleStyleToUse = selectedTitleStyle // Use the special selected style
    }

    // Combine prefix (like "1.") and instance title
    textToRender := fmt.Sprintf(" %d. %s", idx, i.Title)

    // Render the text using the chosen Lipgloss style!
    return titleStyleToUse.Render(textToRender)
}
```
**Explanation:**

*   `import "github.com/charmbracelet/lipgloss"`: This line brings in the Lipgloss library, giving us all its styling powers.
*   `lipgloss.NewStyle()`: This is how you create a new style "recipe" in Lipgloss.
*   `.Padding(...)`, `.Background(...)`, `.Foreground(...)`: These are methods you call on the style object to define how text using this style should look. You specify colors (like `#dde4f0` for a light blue background) and spacing.
*   `titleStyleToUse.Render(textToRender)`: This is the magic! You take your prepared text (`textToRender`) and tell the Lipgloss style to "render" it. Lipgloss then adds all the necessary hidden "escape codes" (special characters that terminals understand) to color and format your text.

The `List` component then takes all these individually styled instance lines and joins them together to form the full list you see on the left side of Claude Squad.

## Internal Implementation: Lipgloss in Action

Every visual part of Claude Squad is a UI component defined in the `ui/` directory. They all follow a similar pattern: they have `SetSize` methods to tell them how much space they have, and `String()` methods that return the final, styled text that Lipgloss generates.

Let's look at a few more examples from the `ui/` directory:

### The `PreviewPane` Component (`ui/preview.go`)

This component displays the main output from the selected AI [Instance](02_instance_.md) (the right side of the screen).

```go
// --- File: ui/preview.go (Simplified) ---
package ui

import (
	"strings"
	"github.com/charmbracelet/lipgloss"
)

var previewPaneStyle = lipgloss.NewStyle().
	Foreground(lipgloss.AdaptiveColor{Light: "#1a1a1a", Dark: "#dddddd"}) // Text color

type PreviewPane struct {
	width  int
	height int
	// ... other fields for content ...
}

// String() method for PreviewPane
func (p *PreviewPane) String() string {
	if p.width == 0 || p.height == 0 {
		return strings.Repeat("\n", p.height) // If no size, just return empty lines
	}

	// This is where dummy content would be; in real code it's from tmux
	content := "This is AI output!\nLine 2 of output."

	// Render the content using the defined style, making sure it fits the width
	rendered := previewPaneStyle.Width(p.width).Render(content)
	return rendered
}
```
**Explanation:**

*   `previewPaneStyle`: Defines a basic text color.
*   `previewPaneStyle.Width(p.width).Render(content)`: Here, `Width(p.width)` is very important. It tells Lipgloss to make sure the rendered text wraps and fills the given width. This ensures the output fits nicely in the pane and doesn't spill over.

### The `DiffPane` Component (`ui/diff.go`)

This component shows the `git diff` output, highlighting additions and deletions.

```go
// --- File: ui/diff.go (Simplified) ---
package ui

import "github.com/charmbracelet/lipgloss"
import "strings"

var (
	AdditionStyle = lipgloss.NewStyle().Foreground(lipgloss.Color("#22c55e")) // Green for additions
	DeletionStyle = lipgloss.NewStyle().Foreground(lipgloss.Color("#ef4444")) // Red for deletions
	HunkStyle     = lipgloss.NewStyle().Foreground(lipgloss.Color("#0ea5e9"))  // Blue for diff hunk headers
)

// colorizeDiff takes raw diff text and applies Lipgloss colors
func colorizeDiff(diff string) string {
	var coloredOutput strings.Builder

	lines := strings.Split(diff, "\n")
	for _, line := range lines {
		if len(line) > 0 {
			if strings.HasPrefix(line, "+") && len(line) > 1 && line[1] != '+' {
				coloredOutput.WriteString(AdditionStyle.Render(line) + "\n")
			} else if strings.HasPrefix(line, "-") && len(line) > 1 && line[1] != '-' {
				coloredOutput.WriteString(DeletionStyle.Render(line) + "\n")
			} else if strings.HasPrefix(line, "@@") {
				coloredOutput.WriteString(HunkStyle.Render(line) + "\n")
			} else {
				coloredOutput.WriteString(line + "\n") // No color for unchanged lines
			}
		}
	}
	return coloredOutput.String()
}
```
**Explanation:**

*   Different `lipgloss.NewStyle()` variables are created for different types of diff lines (additions, deletions, hunk headers).
*   The `colorizeDiff` function loops through each line of the raw `git diff` output.
*   It checks the first character of each line (`+`, `-`, `@@`) to know its type.
*   It then applies the corresponding Lipgloss style using `.Render()` to color that specific line.

### The `Menu` Component (`ui/menu.go`)

This component displays the interactive menu at the bottom, showing available actions.

```go
// --- File: ui/menu.go (Simplified) ---
package ui

import (
	"strings"
	"github.com/charmbracelet/lipgloss"
)

var keyStyle = lipgloss.NewStyle().Foreground(lipgloss.AdaptiveColor{Light: "#655F5F", Dark: "#7F7A7A"}) // Gray key
var descStyle = lipgloss.NewStyle().Foreground(lipgloss.AdaptiveColor{Light: "#7A7474", Dark: "#9C9494"}) // Lighter gray description

var separator = " • " // A common separator character

type Menu struct {
    // ... fields to store menu options ...
}

// String() method for Menu
func (m *Menu) String() string {
	var s strings.Builder

	// Imagine we have options like: [n] New • [q] Quit
	// This loop would go through each option
	s.WriteString(keyStyle.Render("n"))   // Render 'n' key
	s.WriteString(" ")
	s.WriteString(descStyle.Render("New")) // Render 'New' description
	s.WriteString(lipgloss.NewStyle().Foreground(lipgloss.AdaptiveColor{Light:"#DDDADA"}).Render(separator)) // Render separator

	s.WriteString(keyStyle.Render("q"))
	s.WriteString(" ")
	s.WriteString(descStyle.Render("Quit"))

	// Center the whole menu horizontally within its allocated width
	centeredMenuText := lipgloss.NewStyle().Width(m.width).Align(lipgloss.Center).Render(s.String())
	return centeredMenuText
}
```
**Explanation:**

*   `keyStyle` and `descStyle`: Different shades of gray are defined for the key (e.g., `n`) and its description (e.g., `New`).
*   `lipgloss.NewStyle().Width(m.width).Align(lipgloss.Center).Render(s.String())`: This shows how Lipgloss can be used to control the overall layout. It takes all the put-together menu text (`s.String()`), sets its total `Width`, tells it to `Align` to the `Center`, and then renders it.

### Orchestration: How `home` Puts It All Together

The various UI components (`List`, `PreviewPane`, `DiffPane`, `Menu`, `ErrBox`) work mostly independently to style their own content. The [Chapter 1: Main Application (`home` model)](01_main_application___home__model__.md) is the "conductor" that brings them all together.

```mermaid
graph TD
    App[home Model (app/app.go)] --> SetSizeList[List.SetSize()]
    App --> SetSizePreview[PreviewPane.SetSize()]
    App --> SetSizeDiff[DiffPane.SetSize()]
    App --> SetSizeMenu[Menu.SetSize()]
    App --> SetSizeErr[ErrBox.SetSize()]

    App --> View[home.View() method]
    View --> ListString[List.String()]
    View --> PreviewString[PreviewPane.String()]
    View --> DiffString[DiffPane.String()]
    View --> MenuString[Menu.String()]
    View --> ErrString[ErrBox.String()]

    ListString --> LipglossOutputA[Lipgloss Renders List Text]
    PreviewString --> LipglossOutputB[Lipgloss Renders Preview Text]
    DiffString --> LipglossOutputC[Lipgloss Renders Diff Text]
    MenuString --> LipglossOutputD[Lipgloss Renders Menu Text]
    ErrString --> LipglossOutputE[Lipgloss Renders Error Text]

    LipglossOutputA & LipglossOutputB & LipglossOutputC & LipglossOutputD & LipglossOutputE --> FinalScreen[Final Combined Screen Output]
```

1.  **Setting Sizes:** When the Claude Squad window resizes, the `home` model calls the `SetSize()` method on each UI component, telling them how much width and height they have available. This is crucial for components to correctly wrap text and manage their layout.
2.  **`View()` Method:** The `home` model has a special `View()` method. This method is called by the `bubbletea` framework (which Claude Squad uses for its UI) whenever the screen needs to be redrawn.
3.  **Component `String()` Calls:** Inside `home`'s `View()` method, it calls the `String()` method of each UI component (`list.String()`, `tabbedWindow.String()`, `menu.String()`, `errBox.String()`). Each of these calls returns a string that has already been formatted with Lipgloss (colors, borders, padding).
4.  **Joining Them:** The `home` model then uses `lipgloss.JoinHorizontal()` and `lipgloss.JoinVertical()` (or similar methods) to combine all these individual strings into one giant string representing the entire screen.
5.  **Final Output:** This final giant string is then printed to your terminal, and because it contains all the special Lipgloss escape codes, your terminal knows how to display it with the correct colors, layout, and visual flair.

## Conclusion

In this chapter, we explored the concept of **UI Components** in Claude Squad and how they use the **Lipgloss** library to create a visually appealing and organized terminal interface. We learned that UI Components are like building blocks, each responsible for a specific part of the screen (like the list, preview, or menu). They use Lipgloss to apply styles (colors, padding, borders) and manage layout, and the `home` model acts as the conductor, assembling all these components into the final display you see.

Next, we'll dive into how Claude Squad handles its settings and keeps track of ongoing tasks in [Chapter 6: Configuration and State](06_configuration_and_state_.md).

[Next Chapter: Configuration and State](06_configuration_and_state_.md)

---

Generated by [AI Codebase Knowledge Builder](https://github.com/The-Pocket/Tutorial-Codebase-Knowledge)