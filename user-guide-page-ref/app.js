const pages = [
  { title: 'TAIPEI', file: 'taipei.png' },
  { title: 'OSAKA CASTLE', file: 'osaka castle.png' },
  { title: 'SHIBUYA CROSSING', file: 'shibuya crossing.png' },
  { title: 'TOKYO TOWER', file: 'tokyo tower.png' },
  { title: 'TODAI-JI', file: 'todai ji.png' },
  { title: 'GION, KYOTO', file: 'gion kyoto.png' },
  { title: 'KAMAKURA', file: 'kamakura.png' },
  { title: 'ABANDONED CAR, TAIPEI STREET', file: 'abandoned car : taipei street.png' },
  { title: 'STANFORD', file: 'stanford.png' },
];

const assetUrl = (file) => `https://matthewyu.dev/work/sketchbook/${encodeURIComponent(file)}`;
const book = document.querySelector('.book');
const spread = document.querySelector('#paperSpread');
const spreadImage = document.querySelector('.spread-image');
const title = document.querySelector('.caption-title');
const status = document.querySelector('.page-status');
const leaf = document.querySelector('.turn-leaf');
const front = document.querySelector('.leaf-front');
const back = document.querySelector('.leaf-back');
let index = 0;
let busy = false;
let touchStartX = null;

function setSpread(page) {
  spreadImage.src = assetUrl(page.file);
  spreadImage.alt = `${page.title} sketchbook spread`;
}

function render() {
  setSpread(pages[index]);
  title.textContent = pages[index].title;
  status.textContent = `${String(index + 1).padStart(2, '0')} / ${String(pages.length).padStart(2, '0')}`;
  spread.setAttribute('aria-label', `Sketchbook spread: ${pages[index].title}`);
}

function setLeafFace(element, page, side) {
  element.style.backgroundImage = `url("${assetUrl(page.file)}")`;
  element.style.backgroundPosition = side === 'left' ? 'left center' : 'right center';
}

function turn(direction) {
  if (busy) return;
  busy = true;
  const target = (index + direction + pages.length) % pages.length;
  const isReverse = direction < 0;

  leaf.classList.remove('reverse', 'is-turning');
  if (isReverse) leaf.classList.add('reverse');
  setLeafFace(front, pages[index], isReverse ? 'left' : 'right');
  setLeafFace(back, pages[target], isReverse ? 'right' : 'left');
  void leaf.offsetWidth;
  leaf.classList.add('is-turning');
  book.setAttribute('aria-label', `Turning to ${pages[target].title}`);

  const finish = () => {
    index = target;
    render();
    leaf.classList.remove('is-turning', 'reverse');
    leaf.removeEventListener('animationend', finish);
    book.setAttribute('aria-label', 'Interactive sketchbook');
    busy = false;
  };
  leaf.addEventListener('animationend', finish, { once: true });
}

document.querySelector('.previous').addEventListener('click', () => turn(-1));
document.querySelector('.next').addEventListener('click', () => turn(1));
document.addEventListener('keydown', (event) => {
  if (event.key === 'ArrowLeft') turn(-1);
  if (event.key === 'ArrowRight') turn(1);
});
book.addEventListener('touchstart', (event) => {
  touchStartX = event.changedTouches[0].clientX;
}, { passive: true });
book.addEventListener('touchend', (event) => {
  if (touchStartX === null) return;
  const delta = event.changedTouches[0].clientX - touchStartX;
  if (Math.abs(delta) > 45) turn(delta < 0 ? 1 : -1);
  touchStartX = null;
}, { passive: true });
document.querySelector('.scroll-cue').addEventListener('click', () => {
  document.querySelector('.below-fold').scrollIntoView({ behavior: 'smooth' });
});

render();
