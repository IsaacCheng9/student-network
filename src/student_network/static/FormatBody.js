function FormatBody(body) {
  body = markdown.toHTML(body);
  return body.replace(
    /(@(\w+))/gi,
    `<a href="/profile/$2" class="tagged_user">$1</a>`
  );
}
