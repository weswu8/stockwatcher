def click(self, event):
    # get the index of the mouse click
    index = self.MT.index("@%s,%s" % (event.x, event.y))

    # get the indices of all "adj" tags
    tag_indices = list(self.MT.tag_ranges('adj'))

    # iterate them pairwise (start and end index)
    for start, end in zip(tag_indices[0::2], tag_indices[1::2]):
        # check if the tag matches the mouse click index
        if self.MT.compare(start, '<=', index) and self.MT.compare(index, '<', end):
            # return string between tag start and end
            return (start, end, self.MT.get(start, end))