(function () {
	'use strict';

	var modal = document.getElementById('photo-zoom-modal');
	if (!modal) return;

	var backdrop = modal.querySelector('.photo-zoom-backdrop');
	var stage = modal.querySelector('.photo-zoom-stage');
	var imgEl = modal.querySelector('.photo-zoom-img');
	var closeBtn = modal.querySelector('.photo-zoom-close');
	var wrapper = document.getElementById('wrapper');

	var scale = 1;
	var tx = 0;
	var ty = 0;
	var MIN_SCALE = 1;
	var MAX_SCALE = 4;

	var lastPinchDist = 0;
	var lastTouchX = 0;
	var lastTouchY = 0;

	var dragging = false;
	var lastMouseX = 0;
	var lastMouseY = 0;

	function resetTransform() {
		scale = 1;
		tx = 0;
		ty = 0;
		applyTransform();
	}

	function applyTransform() {
		if (scale <= 1.001) {
			scale = 1;
			tx = 0;
			ty = 0;
		}
		stage.style.transform = 'translate(' + tx + 'px, ' + ty + 'px) scale(' + scale + ')';
	}

	function openModal(src, alt) {
		imgEl.src = src;
		imgEl.alt = alt || '';
		resetTransform();
		modal.hidden = false;
		document.body.style.overflow = 'hidden';
		if (wrapper && 'inert' in HTMLElement.prototype) {
			wrapper.inert = true;
		}
		closeBtn.focus();
	}

	function closeModal() {
		modal.hidden = true;
		imgEl.removeAttribute('src');
		imgEl.alt = '';
		document.body.style.overflow = '';
		dragging = false;
		if (wrapper && 'inert' in HTMLElement.prototype) {
			wrapper.inert = false;
		}
		resetTransform();
	}

	function dist(t1, t2) {
		var dx = t1.clientX - t2.clientX;
		var dy = t1.clientY - t2.clientY;
		return Math.sqrt(dx * dx + dy * dy);
	}

	function onTouchStart(e) {
		if (modal.hidden) return;
		if (e.touches.length === 2) {
			lastPinchDist = dist(e.touches[0], e.touches[1]);
		} else if (e.touches.length === 1) {
			lastTouchX = e.touches[0].clientX;
			lastTouchY = e.touches[0].clientY;
		}
	}

	function onTouchMove(e) {
		if (modal.hidden) return;
		if (e.touches.length === 2) {
			e.preventDefault();
			var newDist = dist(e.touches[0], e.touches[1]);
			if (lastPinchDist > 0) {
				var ratio = newDist / lastPinchDist;
				scale *= ratio;
				if (scale < MIN_SCALE) scale = MIN_SCALE;
				if (scale > MAX_SCALE) scale = MAX_SCALE;
				applyTransform();
			}
			lastPinchDist = newDist;
		} else if (e.touches.length === 1 && scale > 1.001) {
			e.preventDefault();
			var x = e.touches[0].clientX;
			var y = e.touches[0].clientY;
			tx += x - lastTouchX;
			ty += y - lastTouchY;
			lastTouchX = x;
			lastTouchY = y;
			applyTransform();
		}
	}

	function onTouchEnd(e) {
		if (modal.hidden) return;
		if (e.touches.length < 2) {
			lastPinchDist = 0;
		}
		if (e.touches.length === 1) {
			lastTouchX = e.touches[0].clientX;
			lastTouchY = e.touches[0].clientY;
		}
		if (e.touches.length === 0) {
			applyTransform();
		}
	}

	modal.addEventListener('touchstart', onTouchStart, { passive: true });
	modal.addEventListener('touchmove', onTouchMove, { passive: false });
	modal.addEventListener('touchend', onTouchEnd, { passive: true });
	modal.addEventListener('touchcancel', onTouchEnd, { passive: true });

	modal.addEventListener('wheel', function (e) {
		if (modal.hidden || (!e.ctrlKey && !e.metaKey)) return;
		e.preventDefault();
		var factor = e.deltaY > 0 ? 0.92 : 1.08;
		scale *= factor;
		if (scale < MIN_SCALE) scale = MIN_SCALE;
		if (scale > MAX_SCALE) scale = MAX_SCALE;
		applyTransform();
	}, { passive: false });

	modal.addEventListener('mousedown', function (e) {
		if (modal.hidden || scale <= 1.001) return;
		if (e.button !== 0) return;
		if (e.target === backdrop || (closeBtn && closeBtn.contains(e.target))) return;
		dragging = true;
		lastMouseX = e.clientX;
		lastMouseY = e.clientY;
	});

	window.addEventListener('mousemove', function (e) {
		if (!dragging || modal.hidden) return;
		tx += e.clientX - lastMouseX;
		ty += e.clientY - lastMouseY;
		lastMouseX = e.clientX;
		lastMouseY = e.clientY;
		applyTransform();
	});

	window.addEventListener('mouseup', function () {
		dragging = false;
	});

	document.addEventListener('click', function (e) {
		var img = e.target && e.target.closest && e.target.closest('img.photo-zoomable');
		if (!img) return;
		e.preventDefault();
		openModal(img.currentSrc || img.src, img.alt);
	});

	document.addEventListener('keydown', function (e) {
		if (e.key === 'Escape' && !modal.hidden) {
			closeModal();
		}
	});

	if (backdrop) backdrop.addEventListener('click', closeModal);
	if (closeBtn) closeBtn.addEventListener('click', closeModal);
})();
