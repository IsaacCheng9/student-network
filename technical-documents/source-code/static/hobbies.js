
	hTags = [];
	hobbyInput = document.getElementsByName('hobbies_input')[0];
	hValues = document.createElement('input');
	hValues.setAttribute('type', 'hidden');
    hValues.setAttribute('name', 'hobbies');
	hobbyInput.appendChild(hValues);
	
    hobbyInput.addEventListener('input', function () {
        let enteredhTags = hobbyInput.value.split(',');
        if (enteredhTags.length > 1) {
            enteredhTags.forEach(function (t) {
                let filteredTag = filterHTag(t);
                if (filteredTag.length > 0)
                    addHTag(filteredTag);
            });
            hobbyInput.value = '';
        }
    });

    hobbyInput.addEventListener('keydown', function (e) {
        let keyCode = e.which || e.keyCode;
        if (keyCode === 8 && hobbyInput.value.length === 0 && hTags.length > 0) {
            removeHTag(hTags.length - 1);
        }
    });


    function addHTag (text) {
        let tag = {
            text: text,
            element: document.createElement('div'),
        };
		
		label = document.createElement('div');
		label.classList.add('ui', 'label');
		label.textContent = tag.text;
		
        tag.element.classList.add('ui','labels', 'teal');
		tag.element.appendChild(label);

        let closeBtn = document.createElement('i');
        closeBtn.classList.add('close', 'icon');
        closeBtn.addEventListener('click', function () {
            removeHTag(hTags.indexOf(tag));
        });
        tag.element.firstElementChild.appendChild(closeBtn);

        hTags.push(tag);

        document.getElementsByName('hobby-div')[0].appendChild(tag.element);

        refreshHTags();
    }

    function removeHTag (index) {
        let tag = hTags[index];
        hTags.splice(index, 1);
        tag.element.remove();
        refreshhTags();
    }

    function refreshHTags () {
        let hTagsList = [];
        hTags.forEach(function (t) {
            hTagsList.push(t.text);
        });
        hValues.value = hTagsList.join(',');
    }

    function filterHTag (tag) {
        return tag.replace(/[^\w -]/g, '').trim().replace(/\W+/g, '-');
    }
