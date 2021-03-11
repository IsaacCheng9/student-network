	iTags = [];
	interestInput = document.getElementsByName('interests_input')[0];
	iValues = document.createElement('input');
	iValues.setAttribute('type', 'hidden');
    iValues.setAttribute('name', 'interests');
	interestInput.appendChild(iValues);
	
    interestInput.addEventListener('input', function () {
        let enterediTags = interestInput.value.split(',');
        if (enterediTags.length > 1) {
            enterediTags.forEach(function (t) {
                let filteredTag = filterITag(t);
                if (filteredTag.length > 0)
                    addITag(filteredTag);
            });
            interestInput.value = '';
        }
    });

    interestInput.addEventListener('keydown', function (e) {
        let keyCode = e.which || e.keyCode;
        if (keyCode === 8 && interestInput.value.length === 0 && iTags.length > 0) {
            removeITag(iTags.length - 1);
        }
    });


    function addITag (text) {
        let tag = {
            text: text,
            element: document.createElement('div'),
        };
		
		label = document.createElement('div');
		label.classList.add('ui', 'label');
		label.textContent = tag.text;
		
        tag.element.classList.add('ui','labels', 'purple');
		tag.element.appendChild(label);

        let closeBtn = document.createElement('i');
        closeBtn.classList.add('close', 'icon');
        closeBtn.addEventListener('click', function () {
            removeITag(iTags.indexOf(tag));
        });
        tag.element.firstElementChild.appendChild(closeBtn);

        iTags.push(tag);

        document.getElementsByName('interest-div')[0].appendChild(tag.element);

        refreshITags();
    }

    function removeITag (index) {
        let tag = iTags[index];
        iTags.splice(index, 1);
        tag.element.remove();
        refreshITags();
    }

    function refreshITags () {
        let iTagsList = [];
        iTags.forEach(function (t) {
            iTagsList.push(t.text);
        });
        iValues.value = iTagsList.join(',');
    }

    function filterITag (tag) {
        return tag.replace(/[^\w -]/g, '').trim().replace(/\W+/g, '-');
    }