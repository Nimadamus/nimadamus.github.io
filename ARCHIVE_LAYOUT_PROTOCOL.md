# Archive Layout Protocol

For legacy BetLegend archive pages that still contain repeated `.blog-post`
cards, every card must remain a sibling block.

Do not leave standalone `</h2>` tags where a `</div>` is required for
`.post-time`, `.share-buttons`, video wrappers, `.verdict`, dropdown wrappers,
or the enclosing `.blog-post`. Nested cards compound their borders and available
width, which collapses the archive into a narrow unreadable column.

Before publishing an archive layout edit, verify:

- `.blog-post` elements are not nested inside other `.blog-post` elements.
- No standalone `</h2>` lines are being used as generic container closers.
- `.post-time` lines close with `</div>`, not `</h2>`.
- The live public archive URL is visually checked in a browser after deploy.