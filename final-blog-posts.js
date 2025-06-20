
fetch('final-blog-posts.json')
  .then(res => res.json())
  .then(data => {
    const urlParams = new URLSearchParams(window.location.search);
    const page = parseInt(urlParams.get('page')) || 1;
    const postsPerPage = 10;
    const start = (page - 1) * postsPerPage;
    const end = start + postsPerPage;

    const postsToShow = data.slice(start, end);
    const blogContainer = document.getElementById('blog-container');

    postsToShow.forEach(post => {
      const wrapper = document.createElement('div');
      wrapper.innerHTML = post.html;
      blogContainer.appendChild(wrapper);
    });

    const totalPages = Math.ceil(data.length / postsPerPage);
    const pagination = document.getElementById('pagination');
    if (totalPages > 1) {
      if (page > 1) {
        const prev = document.createElement('a');
        prev.href = `?page=${page - 1}`;
        prev.textContent = '← Previous';
        prev.style.marginRight = '20px';
        prev.style.color = 'gold';
        pagination.appendChild(prev);
      }
      if (page < totalPages) {
        const next = document.createElement('a');
        next.href = `?page=${page + 1}`;
        next.textContent = 'Next →';
        next.style.color = 'gold';
        pagination.appendChild(next);
      }
    }
  });
